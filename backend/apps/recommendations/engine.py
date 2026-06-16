# apps/recommendations/engine.py
import networkx as nx
from apps.graph.services import GraphService
from apps.skills.models import Skill
from typing import List

class RecommendationEngine:
    def __init__(self):
        self.graph = GraphService()

    def get_next_skills(self, user_skills: List[Skill]) -> List[Dict]:
        """Рекомендует следующие навыки для изучения на основе текущих"""
        if not user_skills:
            return []

        nx_graph = self.graph._nx_graph
        user_skill_names = [skill.name for skill in user_skills]

        recommendations = []
        for skill in user_skills:
            # Находим все навыки, от которых зависит данный
            dependents = list(
                nx_graph.predecessors(skill.name)
            )

            # Навыки, от которых зависит текущий, но которые ещё не освоены
            new_dependencies = [
                dep for dep in dependents
                if dep not in user_skill_names and dep not in [s.name for s in user_skills]
            ]

            for dep in new_dependencies:
                # Проверяем, что это не цикл
                if not self._is_cyclic(nx_graph, dep, skill.name):
                    recommendations.append({
                        "skill": dep,
                        "reason": f"Необходим для {skill.name}",
                        "priority": nx_graph.nodes[dep].get("level_priority", 1)
                    })

        # Находим навыки того же уровня, которые могут быть полезны
        level_skills = {}
        for skill in user_skills:
            level = skill.level
            if level not in level_skills:
                level_skills[level] = []
            level_skills[level].append(skill.name)

        for level, skills in level_skills.items():
            # Находим навыки того же уровня, от которых зависит хотя бы один из освоенных
            similar_level = []
            for dep in nx_graph.nodes:
                if nx_graph.nodes[dep].get("level") == level:
                    for s in skills:
                        if nx_graph.has_edge(dep, s):
                            similar_level.append(dep)
                            break

            # Добавляем рекомендации
            for s in similar_level:
                if s not in user_skill_names:
                    recommendations.append({
                        "skill": s,
                        "reason": f"Уровень {level}, может быть полезен",
                        "priority": nx_graph.nodes[s].get("level_priority", 1)
                    })

        # Сортируем по приоритету
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations[:5]

    def _is_cyclic(self, graph: nx.DiGraph, start: str, end: str) -> bool:
        """Проверяет наличие циклов между двумя узлами"""
        path = nx.shortest_path(graph, start, end)
        if len(path) >= 2:
            for i in range(len(path) - 1):
                if path[i] == end and path[i+1] == start:
                    return True
        return False
