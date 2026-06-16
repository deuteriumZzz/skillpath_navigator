from django.test import TestCase

from apps.skills.models import Skill

from .schema import schema


class GraphQLSchemaTestCase(TestCase):
    def test_schema_builds(self):
        self.assertIsNotNone(schema)

    def test_query_skills(self):
        Skill.objects.create(name='Python', level='beginner')
        result = schema.execute('{ skills { name level } }')
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['skills'][0]['name'], 'Python')

    def test_query_skill_graph(self):
        Skill.objects.create(name='Python', level='beginner')
        result = schema.execute('{ skillGraph { nodes { name level } edges { from to type } } }')
        self.assertIsNone(result.errors)
