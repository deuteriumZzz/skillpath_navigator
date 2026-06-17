"""
GraphService — фасад над графом навыков. Алгоритмы (поиск пути, проверка готовности
двигаться дальше по графу) реализованы здесь один раз и работают одинаково независимо
от того, какой backend хранит данные (Neo4j или in-memory networkx).
"""

from typing import Any, Dict, List, Optional

import logging

import networkx as nx
from django.conf import settings

from apps.graph.backends import GraphBackend, InMemoryGraphBackend, Neo4jGraphBackend
from core.constants import RELATION_TYPES, SKILL_LEVELS

# Единый in-memory граф на процесс, чтобы данные не терялись между запросами/тестами
# при GRAPH_BACKEND=memory (аналог "БД в памяти" для dev-режима без Neo4j).
_shared_memory_backend: Optional[InMemoryGraphBackend] = None
_memory_backend_warned = False

_logger = logging.getLogger(__name__)


def _default_backend() -> GraphBackend:
    global _shared_memory_backend, _memory_backend_warned
    if settings.GRAPH_BACKEND == "neo4j":
        return Neo4jGraphBackend(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    if not settings.DEBUG and not _memory_backend_warned:
        _logger.warning(
            "GRAPH_BACKEND=memory in production (DEBUG=False). "
            "Each gunicorn worker holds a separate in-memory graph — "
            "set GRAPH_BACKEND=neo4j for production."
        )
        _memory_backend_warned = True
    if _shared_memory_backend is None:
        _shared_memory_backend = InMemoryGraphBackend()
    return _shared_memory_backend


class GraphService:
    def __init__(self, backend: Optional[GraphBackend] = None) -> None:
        self.backend = backend or _default_backend()
        self.refresh()

    def refresh(self) -> None:
        """Перестраивает локальный networkx-граф из хранилища backend'а."""
        self._nx_graph = self.backend.load_networkx_graph()

    # --- Запись ---

    def add_skill_to_graph(self, name: str, level: str = "beginner") -> bool:
        self.backend.persist_skill(name, level)
        self._nx_graph.add_node(name, level=level, type="Skill")
        return True

    def add_dependency(self, skill: str, depends_on: str, relation_type: str = "DEPENDS_ON") -> bool:
        """Помечает, что `skill` зависит от `depends_on` (depends_on нужно изучить раньше)."""
        if relation_type not in RELATION_TYPES:
            raise ValueError(f"Недопустимый тип связи: {relation_type}")
        self.backend.persist_dependency(depends_on, skill, relation_type)
        self._nx_graph.add_edge(depends_on, skill, type=relation_type)
        from django.core.cache import cache
        from core.constants import SKILL_GRAPH_CACHE_KEY
        cache.delete(SKILL_GRAPH_CACHE_KEY)
        return True

    # --- Чтение ---

    def has_skill(self, name: str) -> bool:
        return name in self._nx_graph

    def get_skill_level(self, name: str) -> Optional[str]:
        if name not in self._nx_graph:
            return None
        return self._nx_graph.nodes[name].get("level")

    def find_skills_by_level(self, level: str, limit: int = 10) -> List[str]:
        return [n for n, data in self._nx_graph.nodes(data=True) if data.get("level") == level][:limit]

    def get_prerequisites(self, skill_name: str) -> List[str]:
        """Навыки, которые нужно изучить до `skill_name` (прямые зависимости)."""
        if skill_name not in self._nx_graph:
            return []
        return list(self._nx_graph.predecessors(skill_name))

    def get_unlocked_by(self, skill_name: str) -> List[str]:
        """Навыки, для которых `skill_name` является прямой предпосылкой ("next steps")."""
        if skill_name not in self._nx_graph:
            return []
        return list(self._nx_graph.successors(skill_name))

    def get_skill_dependencies(self, skill_name: str) -> List[Dict[str, str]]:
        """Все связи навыка: и его предпосылки, и навыки, разблокируемые им."""
        if skill_name not in self._nx_graph:
            return []
        result = []
        for prereq in self._nx_graph.predecessors(skill_name):
            result.append({"relation_type": "REQUIRES", "related_skill": prereq, "level": self.get_skill_level(prereq)})
        for unlocked in self._nx_graph.successors(skill_name):
            result.append({"relation_type": "UNLOCKS", "related_skill": unlocked, "level": self.get_skill_level(unlocked)})
        return result

    def can_proceed(self, skill_name: str, known_skills: List[str]) -> Dict[str, Any]:
        """Проверяет, хватает ли пользователю навыков, чтобы перейти к `skill_name`."""
        prerequisites = self.get_prerequisites(skill_name)
        known = set(known_skills)
        missing = [p for p in prerequisites if p not in known]
        return {
            "can_proceed": len(missing) == 0,
            "missing_skills": missing,
            "required_skills": prerequisites,
        }

    def _edge_weight(self, u: str, v: str) -> float:
        """Вес ребра (u → v): 1.0 плюс разница индексов уровней сложности навыков.
        Чем больше «прыжок» по уровню, тем дороже переход при поиске кратчайшего пути.
        """
        level_u = self.get_skill_level(u)
        level_v = self.get_skill_level(v)
        if level_u not in SKILL_LEVELS or level_v not in SKILL_LEVELS:
            return 1.0
        return 1.0 + abs(SKILL_LEVELS.index(level_u) - SKILL_LEVELS.index(level_v))

    def find_shortest_path(
        self,
        start_skill: str,
        end_skill: str,
        weighted_by_level: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if start_skill == end_skill:
            if start_skill not in self._nx_graph:
                return None
            return {
                "path": [start_skill],
                "distance": 0.0,
                "weights": [],
                "levels": [self.get_skill_level(start_skill)],
            }

        if start_skill not in self._nx_graph or end_skill not in self._nx_graph:
            return None

        try:
            if weighted_by_level:
                for u, v in self._nx_graph.edges():
                    self._nx_graph[u][v]["weight"] = self._edge_weight(u, v)
                path = nx.shortest_path(self._nx_graph, start_skill, end_skill, weight="weight")
                distance = nx.shortest_path_length(self._nx_graph, start_skill, end_skill, weight="weight")
                weights = [self._nx_graph[path[i]][path[i + 1]]["weight"] for i in range(len(path) - 1)]
            else:
                path = nx.shortest_path(self._nx_graph, start_skill, end_skill)
                distance = float(len(path) - 1)
                weights = [1.0] * (len(path) - 1)
        except nx.NetworkXNoPath:
            return None

        return {
            "path": path,
            "distance": distance,
            "weights": weights,
            "levels": [self.get_skill_level(node) for node in path],
        }

    def find_all_possible_paths(
        self,
        start_skill: str,
        end_skill: str,
        max_paths: int = 3,
    ) -> List[Dict[str, Any]]:
        """Возвращает до `max_paths` простых путей от start_skill до end_skill,
        отсортированных по длине (числу шагов). Каждый путь включает веса рёбер
        и уровни навыков в узлах.
        """
        if start_skill not in self._nx_graph or end_skill not in self._nx_graph:
            return []

        all_paths = list(nx.all_simple_paths(self._nx_graph, start_skill, end_skill))
        all_paths = sorted(all_paths, key=len)[:max_paths]

        result = []
        for path in all_paths:
            weights = [self._edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
            result.append({
                "path": path,
                "distance": sum(weights),
                "weights": weights,
                "levels": [self.get_skill_level(node) for node in path],
            })
        return result

    def to_graph_payload(self) -> Dict[str, Any]:
        """Полное представление графа для GET /api/skills/graph/."""
        nodes = [
            {"id": name, "name": name, "level": data.get("level")}
            for name, data in self._nx_graph.nodes(data=True)
        ]
        edges = [
            {"from": u, "to": v, "type": data.get("type", "DEPENDS_ON")}
            for u, v, data in self._nx_graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}


def add_skill_to_graph(name: str, level: str = "beginner") -> bool:
    return GraphService().add_skill_to_graph(name, level)


def add_dependency(skill: str, depends_on: str, relation_type: str = "DEPENDS_ON") -> bool:
    return GraphService().add_dependency(skill, depends_on, relation_type)
