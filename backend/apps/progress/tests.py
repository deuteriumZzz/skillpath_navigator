from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.skills.models import Skill

from .models import UserSkillProgress

User = get_user_model()


class UserSkillProgressTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='pass12345')
        self.skill = Skill.objects.create(name='Django ORM', level='intermediate')

    def test_progress_percent_bounds(self):
        progress = UserSkillProgress.objects.create(user=self.user, skill=self.skill, completion_percent=50)
        self.assertEqual(progress.completion_percent, 50)

    def test_unique_per_user_skill(self):
        UserSkillProgress.objects.create(user=self.user, skill=self.skill, completion_percent=10)
        with self.assertRaises(Exception):
            UserSkillProgress.objects.create(user=self.user, skill=self.skill, completion_percent=20)
