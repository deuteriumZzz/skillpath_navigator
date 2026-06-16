from django.test import TestCase
from apps.graph.services import GraphService
from apps.skills.models import Skill
from unittest.mock import patch
import networkx as nx
import json

class GraphServiceTestCase(TestCase):
    def setUp(self):
        self.graph = GraphService()
        self.test_skills = [
            "Python Basics", "Python Intermediate", "Python Advanced", "Machine Learning",
            "Deep Learning", "Data Visualization"
        ]
        for skill in self.test_skills:
            Skill.objects.create(name=skill, level="beginner", owner=self.user)

        # Добавляем зависимости
        self.graph.add_dependency("Python Basics", "Python Intermediate")
        self.graph.add_dependency("Python Intermediate", "Python Advanced")
        self.graph.add_dependency("Python Advanced", "Machine Learning")
        self.graph.add_dependency("Machine Learning", "Deep Learning")
        self.graph.add_dependency("Python Basics", "Data Visualization")

    def test_add_skill_to_graph(self):
        self.graph.add_skill_to_graph("New Skill", "intermediate")
        self.assertTrue(self.graph._nx_graph.has_node("New Skill"))

    def test_find_shortest_path(self):
        path = self.graph.find_shortest_path("Python Basics", "Deep Learning")
        self.assertIsNotNone(path)
        self.assertEqual(path["path"], [
            "Python Basics", "Python Intermediate", "Python Advanced",
            "Machine Learning", "Deep Learning"
        ])

        path = self.graph.find_shortest_path("Python Basics", "Data Visualization")
        self.assertIsNotNone(path)
        self.assertEqual(path["path"], ["Python Basics", "Data Visualization"])

        path = self.graph.find_shortest_path("Deep Learning", "Python Basics")
        self.assertIsNone(path)

    def test_weighted_path(self):
        # Обновляем уровни навыков для теста
        self.graph.add_skill_to_graph("Python Basics", "beginner")
        self.graph.add_skill_to_graph("Python Intermediate", "intermediate")
        self.graph.add_skill_to_graph("Python Advanced", "advanced")
        self.graph.add_skill_to_graph("Machine Learning", "advanced")
        self.graph.add_skill_to_graph("Deep Learning", "expert")

        path = self.graph.find_shortest_path(
            "Python Basics",
            "Deep Learning",
            weighted_by_level=True
        )
        self.assertIsNotNone(path)
        self.assertGreater(path["distance"], 
        self.assertGreaterEqual(path["weights"][0], 1.0)  # Python Basics -> Intermediate

    def test_find_all_possible_paths(self):
        # Тестируем поиск всех возможных путей
        paths = self.graph.find_all_possible_paths(
            "Python Basics",
            "Data Visualization",
            max_paths=2
        )
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]["path"]), 2)

    def test_skill_dependencies(self):
        dependencies = self.graph.get_skill_dependencies("Python Intermediate")
        self.assertEqual(len(dependencies), 2)  # DEPENDS_ON: Python Basics + DEPENDS_ON_BY: Python Advanced
        for dep in dependencies:
            self.assertIn(dep["relation_type"], ["DEPENDS_ON", "DEPENDS_ON_BY"])

    @patch.object(GraphService, '_build_networkx_graph')
    def test_graph_initialization(self, mock_build):
        mock_build.return_value = nx.DiGraph()
        service = GraphService()
        self.assertIsInstance(service._nx_graph, nx.DiGraph)
