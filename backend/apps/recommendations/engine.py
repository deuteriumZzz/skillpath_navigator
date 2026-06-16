from apps.graph.services import execute_query
from apps.skills.models import Skill
from apps.recommendations.utils import SkillLevelAnalyzer

class RecommendationEngine:
    def __init__(self):
        self.analyzer = SkillLevelAnalyzer()

    def get_next_skills(self, user_skills, limit=5):
        """Рекомендует следующие навыки для освоения"""
        user_skill_names = [skill.name for skill in user_skills]
        query = """
        MATCH (s:Skill {name: $skill})-[r:DEPENDS_ON]->(next_skill)
        WHERE NOT next_skill.name IN $user_skills
        RETURN DISTINCT next_skill.name AS name, next_skill.level AS level
        ORDER BY next_skill.level
        LIMIT $limit
        """
        results = execute_query(query, {
            'skill': user_skill_names[0],
            'user_skills': user_skill_names,
            'limit': limit
        })
        return [{"name": r["name"], "level": r["level"]} for r in results]

    def find_learning_path(self, start_skill, end_skill):
        """Находит кратчайший путь между навыками"""
        query = """
        MATCH path = shortestPath(($start)-[*]->($end))
        RETURN nodes(path) AS nodes
        """
        results = execute_query(query, {
            'start': {'name': start_skill},
            'end': {'name': end_skill}
        })

        if not results:
            return None

        path = [node["nodes"][0]["name"] for node in results[0]["nodes"]]
        return path

    def find_gaps(self, user_skills):
        """Определяет пробелы в знаниях пользователя"""
        user_skill_names = [skill.name for skill in user_skills]
        query = """
        MATCH (s:Skill)-[r:DEPENDS_ON]->(missing)
        WHERE NOT missing.name IN $user_skills
        RETURN DISTINCT missing.name AS name, missing.level AS level
        ORDER BY missing.level
        """
        results = execute_query(query, {'user_skills': user_skill_names})
        return [{"name": r["name"], "level": r["level"]} for r in results]

    def analyze_skill(self, skill_description):
        """Анализирует описание навыка и предлагает уровень"""
        level = self.analyzer.analyze(skill_description)
        return {"level": level, "confidence": self.analyzer.classifier(skill_description[:512])[0]["score"]}
