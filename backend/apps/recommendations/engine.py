from typing import Any, Dict, List, Optional

from apps.graph.services import GraphService
from core.constants import SKILL_LEVELS


class RecommendationEngine:
    """Рекомендации следующих навыков и путей обучения на основе графа навыков."""

    def __init__(self, graph: Optional[GraphService] = None) -> None:
        self.graph = graph or GraphService()

    def get_next_skills(
        self, known_skill_names: List[str], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Навыки, которые пользователь уже может изучать (все их предпосылки выполнены)."""
        known = set(known_skill_names)
        candidates: Dict[str, Dict[str, Any]] = {}

        for skill_name in known_skill_names:
            for unlocked in self.graph.get_unlocked_by(skill_name):
                if unlocked in known or unlocked in candidates:
                    continue
                readiness = self.graph.can_proceed(unlocked, known_skill_names)
                if not readiness["can_proceed"]:
                    continue
                candidates[unlocked] = {
                    "skill": unlocked,
                    "level": self.graph.get_skill_level(unlocked),
                    "reason": f"Открыт благодаря «{skill_name}»",
                }

        recommendations = list(candidates.values())
        recommendations.sort(
            key=lambda r: SKILL_LEVELS.index(r["level"])
            if r["level"] in SKILL_LEVELS
            else 0
        )
        return recommendations[:limit]

    def find_learning_path(
        self, start_skill: str, end_skill: str
    ) -> Optional[Dict[str, Any]]:
        return self.graph.find_shortest_path(start_skill, end_skill)

    def check_readiness(
        self, skill_name: str, known_skill_names: List[str]
    ) -> Dict[str, Any]:
        """Может ли пользователь двигаться дальше к `skill_name` с текущим набором навыков."""
        return self.graph.can_proceed(skill_name, known_skill_names)
