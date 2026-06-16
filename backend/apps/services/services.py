from py2neo import Graph, Node, Relationship
from django.conf import settings
from typing import List, Optional, Dict, Any
import networkx as nx
import json
from functools import lru_cache

class GraphService:
    def __init__(self):
        self.graph = Graph(
            f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}",
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self._nx_graph = self._build_networkx_graph()  # Создаём граф NetworkX для аналитики

    def _build_networkx_graph(self) -> nx.DiGraph:
        """Строит граф NetworkX из данных Neo4j для удобного поиска путей"""
        G = nx.DiGraph()

        # Получаем все узлы Skill
        query = "MATCH (s:Skill) RETURN s.name AS name, s.level AS level"
        for record in self.graph.run(query).data():
            G.add_node(record['name'], level=record['level'], type="Skill")

        # Получаем зависимости DEPENDS_ON
        query = """
        MATCH (a:Skill)-[:DEPENDS_ON]->(b:Skill)
        RETURN a.name AS source, b.name AS target
        """
        for record in self.graph.run(query).data():
            G.add_edge(record['source'], record['target'], type="DEPENDS_ON")

        # Получаем обратные зависимости DEPENDS_ON_BY
        query = """
        MATCH (a:Skill)<-[:DEPENDS_ON]-(b:Skill)
        RETURN b.name AS source, a.name AS target
        """
        for record in self.graph.run(query).data():
            G.add_edge(record['source'], record['target'], type="DEPENDS_ON_BY")

        return G

    def add_skill_to_graph(self, name: str, level: str) -> bool:
        """Добавляет узел навыка в граф Neo4j и обновляет NetworkX граф"""
        query = """
        MERGE (s:Skill {name: $name})
        SET s.level = $level
        RETURN s
        """
        self.graph.run(query, name=name, level=level)
        self._nx_graph.add_node(name, level=level, type="Skill")
        return True

    def add_dependency(self, skill1: str, skill2: str, relation_type: str = "DEPENDS_ON") -> bool:
        """Добавляет зависимость между навыками с указанием типа связи"""
        query = """
        MATCH (a:Skill {name: $skill1}), (b:Skill {name: $skill2})
        MERGE (a)-[r:%s]->(b)
        """ % relation_type

        self.graph.run(query, skill1=skill1, skill2=skill2)
        self._nx_graph.add_edge(skill1, skill2, type=relation_type)
        return True

    def find_shortest_path(
        self,
        start_skill: str,
        end_skill: str,
        weighted_by_level: bool = True,
        allow_indirect: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Находит кратчайший путь между навыками с учётом:
        - Уровней сложности (по умолчанию учитывается)
        - Непосредственных зависимостей (DEPENDS_ON)
        - Обратных зависимостей (DEPENDS_ON_BY) при allow_indirect=True

        Возвращает:
        - "path": [skill1, skill2, ...] - путь в виде списка имён навыков
        - "distance": float - длина пути (сумма весов)
        - "weights": [weight1, weight2, ...] - веса рёбер
        - "levels": [level1, level2, ...] - уровни навыков на пути
        """
        if start_skill == end_skill:
            return {
                "path": [start_skill],
                "distance": 0.0,
                "weights": [],
                "levels": [self.get_skill_level(start_skill)]
            }

        # Проверяем существование узлов
        if start_skill not in self._nx_graph or end_skill not in self._nx_graph:
            return None

        # Если не учитывать веса, используем BFS
        if not weighted_by_level:
            try:
                path = nx.shortest_path(self._nx_graph, start_skill, end_skill)
                return {
                    "path": path,
                    "distance": len(path) - 1,
                    "weights": [1] * (len(path) - 1),
                    "levels": [self.get_skill_level(node) for node in path]
                }
            except nx.NetworkXNoPath:
                return None

        # Иначе используем алгоритм Дейкстры с учётом весов
        try:
            # Задаём веса рёбер с учётом разницы уровней
            for u, v, data in self._nx_graph.edges(data=True):
                level_u = self.get_skill_level(u)
                level_v = self.get_skill_level(v)

                # Вес = 1 + разница уровней (высший уровень -> сложнее)
                if level_u == level_v:
                    self._nx_graph[u][v]["weight"] = 1.0
                elif level_u == "beginner" and level_v in ["intermediate", "advanced"]:
                    self._nx_graph[u][v]["weight"] = 1.5
                elif level_u in ["intermediate", "advanced"] and level_v == "expert":
                    self._nx_graph[u][v]["weight"] = 2.0
                else:
                    self._nx_graph[u][v]["weight"] = 1.0 + abs(
                        ["beginner", "intermediate", "advanced", "expert"].index(level_u) -
                        ["beginner", "intermediate", "advanced", "expert"].index(level_v)
                    )

            # Поиск пути с минимальным весом
            path = nx.shortest_path(
                self._nx_graph,
                start_skill,
                end_skill,
                weight="weight"
            )
            path_length = nx.shortest_path_length(
                self._nx_graph,
                start_skill,
                end_skill,
                weight="weight"
            )

            # Восстановление весов рёбер
            weights = []
            for i in range(len(path) - 1):
                weights.append(self._nx_graph[path[i]][path[i+1]]["weight"])

            return {
                "path": path,
                "distance": path_length,
                "weights": weights,
                "levels": [self.get_skill_level(node) for node in path]
            }
        except nx.NetworkXNoPath:
            return None

    def find_all_possible_paths(
        self,
        start_skill: str,
        end_skill: str,
        max_paths: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Находит все возможные пути между навыками (с учетом обратных зависимостей)
        и возвращает топ-N путей по длине.
        """
        if start_skill not in self._nx_graph or end_skill not in self._nx_graph:
            return []

        # Поиск всех простых путей (без циклов)
        all_paths = list(nx.all_simple_paths(self._nx_graph, start_skill, end_skill))

        # Если путей слишком много, ограничиваем
        if len(all_paths) > max_paths:
            all_paths = sorted(
                all_paths,
                key=lambda p: len(p)
            )[:max_paths]
        else:
            all_paths = all_paths[:max_paths]

        # Формируем результат
        result = []
        for path in all_paths:
            weights = []
            total_weight = 0.0
            levels = []

            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                level_u = self.get_skill_level(u)
                level_v = self.get_skill_level(v)

                # Рассчитываем вес ребра
                if level_u == level_v:
                    weight = 1.0
                else:
                    weight = 1.0 + abs(
                        ["beginner", "intermediate", "advanced", "expert"].index(level_u) -
                        ["beginner", "intermediate", "advanced", "expert"].index(level_v)
                    )
                weights.append(weight)
                total_weight += weight
                levels.append(level_u)

            levels.append(self.get_skill_level(path[-1]))

            result.append({
                "path": path,
                "distance": total_weight,
                "weights": weights,
                "levels": levels
            })

        return result

    def find_skills_by_level(self, level: str, limit: int = 10) -> List[str]:
        """Возвращает список навыков заданного уровня"""
        query = f"""
        MATCH (s:Skill)
        WHERE s.level = '{level}'
        RETURN s.name AS name
        LIMIT {limit}
        """
        result = self.graph.run(query).data()
        return [item['name'] for item in result]

    def get_skill_dependencies(self, skill_name: str) -> List[Dict[str, str]]:
        """Возвращает все зависимости навыка (как прямые, так и обратные)"""
        query = """
        MATCH (s:Skill {name: $name})-[:DEPENDS_ON|DEPENDS_ON_BY]-(related)
        RETURN
            CASE WHEN exists((s)-[:DEPENDS_ON]->(related)) THEN 'DEPENDS_ON' ELSE 'DEPENDS_ON_BY' END AS relation_type,
            related.name AS related_skill,
            related.level AS level
        """
        result = self.graph.run(query, name=skill_name).data()
        return result
