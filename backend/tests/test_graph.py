from apps.graph.backends import InMemoryGraphBackend
from apps.graph.services import GraphService
from django.test import TestCase


class GraphServiceTestCase(TestCase):
    def setUp(self):
        # Каждый тест получает свой изолированный backend — без расшаривания
        # состояния между тестами (в отличие от старого/сломанного теста).
        self.graph = GraphService(backend=InMemoryGraphBackend())

        levels = {
            "Python Basics": "beginner",
            "Python Intermediate": "intermediate",
            "Python Advanced": "advanced",
            "Machine Learning": "advanced",
            "Deep Learning": "expert",
            "Data Visualization": "intermediate",
        }
        for name, level in levels.items():
            self.graph.add_skill_to_graph(name, level)

        self.graph.add_dependency("Python Intermediate", "Python Basics")
        self.graph.add_dependency("Python Advanced", "Python Intermediate")
        self.graph.add_dependency("Machine Learning", "Python Advanced")
        self.graph.add_dependency("Deep Learning", "Machine Learning")
        self.graph.add_dependency("Data Visualization", "Python Basics")

    def test_add_skill_to_graph(self):
        self.graph.add_skill_to_graph("New Skill", "intermediate")
        self.assertTrue(self.graph.has_skill("New Skill"))

    def test_find_shortest_path(self):
        path = self.graph.find_shortest_path("Python Basics", "Deep Learning")
        self.assertIsNotNone(path)
        self.assertEqual(
            path["path"],
            [
                "Python Basics",
                "Python Intermediate",
                "Python Advanced",
                "Machine Learning",
                "Deep Learning",
            ],
        )

        path = self.graph.find_shortest_path("Python Basics", "Data Visualization")
        self.assertIsNotNone(path)
        self.assertEqual(path["path"], ["Python Basics", "Data Visualization"])

        # Обратного пути нет — Deep Learning не является предпосылкой Python Basics
        path = self.graph.find_shortest_path("Deep Learning", "Python Basics")
        self.assertIsNone(path)

    def test_weighted_path(self):
        path = self.graph.find_shortest_path(
            "Python Basics", "Deep Learning", weighted_by_level=True
        )
        self.assertIsNotNone(path)
        self.assertGreater(path["distance"], 0)
        self.assertGreaterEqual(path["weights"][0], 1.0)

    def test_find_all_possible_paths(self):
        paths = self.graph.find_all_possible_paths(
            "Python Basics", "Data Visualization", max_paths=2
        )
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["path"], ["Python Basics", "Data Visualization"])

    def test_skill_dependencies(self):
        dependencies = self.graph.get_skill_dependencies("Python Intermediate")
        relation_types = {dep["relation_type"] for dep in dependencies}
        self.assertEqual(relation_types, {"REQUIRES", "UNLOCKS"})

    def test_can_proceed(self):
        result = self.graph.can_proceed(
            "Python Advanced", known_skills=["Python Basics"]
        )
        self.assertFalse(result["can_proceed"])
        self.assertIn("Python Intermediate", result["missing_skills"])

        result = self.graph.can_proceed(
            "Python Advanced", known_skills=["Python Basics", "Python Intermediate"]
        )
        self.assertTrue(result["can_proceed"])
        self.assertEqual(result["missing_skills"], [])

    def test_invalid_relation_type_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.add_dependency(
                "Python Advanced", "Python Basics", relation_type="DROP TABLE"
            )
