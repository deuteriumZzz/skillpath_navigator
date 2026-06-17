from unittest.mock import MagicMock

from apps.graph.backends import InMemoryGraphBackend
from apps.graph.services import GraphService
from apps.recommendations.engine import RecommendationEngine
from apps.recommendations.llm_analyzer import SkillTextAnalyzer
from django.test import TestCase


class RecommendationEngineTestCase(TestCase):
    def setUp(self):
        self.graph = GraphService(backend=InMemoryGraphBackend())
        self.graph.add_skill_to_graph("Python", "beginner")
        self.graph.add_skill_to_graph("Django", "intermediate")
        self.graph.add_skill_to_graph("SQL", "beginner")
        self.graph.add_dependency("Django", "Python")
        self.graph.add_dependency("Django", "SQL")
        self.engine = RecommendationEngine(graph=self.graph)

    def test_get_next_skills_requires_all_prerequisites(self):
        recs = self.engine.get_next_skills(["Python"])
        self.assertEqual(recs, [])  # SQL ещё не освоен, Django пока недоступен

    def test_get_next_skills_unlocks_when_ready(self):
        recs = self.engine.get_next_skills(["Python", "SQL"])
        self.assertEqual([r["skill"] for r in recs], ["Django"])

    def test_find_learning_path(self):
        path = self.engine.find_learning_path("Python", "Django")
        self.assertIsNotNone(path)
        self.assertIn("Python", path["path"])
        self.assertIn("Django", path["path"])

    def test_check_readiness(self):
        result = self.engine.check_readiness("Django", ["Python"])
        self.assertFalse(result["can_proceed"])
        self.assertIn("SQL", result["missing_skills"])


class SkillTextAnalyzerTestCase(TestCase):
    def test_fallback_without_api_key(self):
        analyzer = SkillTextAnalyzer(client=None)
        result = analyzer.analyze("Python продвинутый уровень, основы SQL")
        names = [r["name"] for r in result]
        self.assertTrue(any("Python" in n for n in names))

    def test_uses_llm_client_when_available(self):
        mock_client = MagicMock()
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.input = {"skills": [{"name": "Python", "level": "advanced"}]}
        mock_client.messages.create.return_value = MagicMock(content=[tool_block])

        analyzer = SkillTextAnalyzer(client=mock_client)
        result = analyzer.analyze("Я эксперт в Python")
        self.assertEqual(result, [{"name": "Python", "level": "advanced"}])
        mock_client.messages.create.assert_called_once()
