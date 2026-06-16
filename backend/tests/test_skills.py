from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.graph.services import GraphService
from apps.skills.models import Skill, UserSkill

User = get_user_model()


class SkillModelTestCase(TestCase):
    def test_skill_creation_adds_to_graph(self):
        skill = Skill.objects.create(name='Rust', level='advanced')
        self.assertTrue(GraphService().has_skill(skill.name))

    def test_user_skill_unique_per_user_and_skill(self):
        user = User.objects.create_user(username='dave', email='dave@example.com', password='pass12345')
        skill = Skill.objects.create(name='Go', level='intermediate')
        UserSkill.objects.create(user=user, skill=skill, level='intermediate')
        with self.assertRaises(Exception):
            UserSkill.objects.create(user=user, skill=skill, level='advanced')
