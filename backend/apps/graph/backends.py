"""
Бэкенды хранения графа навыков.

Граф представляет собой ориентированный граф, где ребро (prerequisite -> skill)
означает «prerequisite нужно изучить раньше, чем skill» (skill зависит от prerequisite).
Это направление выбрано так, чтобы путь от базового навыка к целевому совпадал
с порядком обучения и естественно искался через networkx.shortest_path(start, end).
"""

from abc import ABC, abstractmethod

import networkx as nx


class GraphBackend(ABC):
    """Интерфейс хранения графа навыков. Алгоритмы (поиск пути, проверка готовности)
    реализованы один раз в GraphService и работают с networkx-представлением,
    которое backend обязан уметь строить из своего хранилища."""

    @abstractmethod
    def persist_skill(self, name: str, level: str) -> None:
        ...

    @abstractmethod
    def persist_dependency(
        self, prerequisite: str, skill: str, relation_type: str
    ) -> None:
        ...

    @abstractmethod
    def load_networkx_graph(self) -> nx.DiGraph:
        ...


class InMemoryGraphBackend(GraphBackend):
    """Граф целиком живёт в памяти процесса. Используется в dev/тестах без поднятого Neo4j."""

    def __init__(self) -> None:
        self._graph = nx.DiGraph()

    def persist_skill(self, name: str, level: str) -> None:
        self._graph.add_node(name, level=level, type="Skill")

    def persist_dependency(
        self, prerequisite: str, skill: str, relation_type: str
    ) -> None:
        if prerequisite not in self._graph:
            self._graph.add_node(prerequisite, level="beginner", type="Skill")
        if skill not in self._graph:
            self._graph.add_node(skill, level="beginner", type="Skill")
        self._graph.add_edge(prerequisite, skill, type=relation_type)

    def load_networkx_graph(self) -> nx.DiGraph:
        return self._graph


class Neo4jGraphBackend(GraphBackend):
    """Хранение графа в Neo4j. networkx-граф строится из Neo4j при каждом обращении
    к GraphService.refresh(), чтобы алгоритмы поиска пути работали локально и быстро."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def persist_skill(self, name: str, level: str) -> None:
        with self._driver.session() as session:
            session.run(
                "MERGE (s:Skill {name: $name}) SET s.level = $level",
                name=name,
                level=level,
            )

    def persist_dependency(
        self, prerequisite: str, skill: str, relation_type: str
    ) -> None:
        query = (
            "MERGE (p:Skill {name: $prerequisite}) "
            "MERGE (s:Skill {name: $skill}) "
            f"MERGE (p)-[:{relation_type}]->(s)"
        )
        with self._driver.session() as session:
            session.run(query, prerequisite=prerequisite, skill=skill)

    def load_networkx_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        with self._driver.session() as session:
            for record in session.run(
                "MATCH (s:Skill) RETURN s.name AS name, s.level AS level"
            ):
                graph.add_node(record["name"], level=record["level"], type="Skill")
            for record in session.run(
                "MATCH (p:Skill)-[r]->(s:Skill) RETURN p.name AS source, s.name AS target, type(r) AS rel"
            ):
                graph.add_edge(record["source"], record["target"], type=record["rel"])
        return graph

    def close(self) -> None:
        self._driver.close()
