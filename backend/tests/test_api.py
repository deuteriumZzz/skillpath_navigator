from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.graph.services import GraphService
from apps.skills.models import Skill, UserSkill

User = get_user_model()


class ApiEndpointsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bob', email='bob@example.com', password='pass12345')
        self.client.force_authenticate(self.user)

        self.python = Skill.objects.create(name='Python', level='beginner')
        self.django = Skill.objects.create(name='Django', level='intermediate')
        GraphService().add_dependency('Django', 'Python')

        UserSkill.objects.create(user=self.user, skill=self.python, level='beginner')

    def test_skill_graph(self):
        response = self.client.get('/api/v1/skills/graph/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('nodes', response.data)
        self.assertIn('edges', response.data)

    def test_next_step(self):
        response = self.client.get(f'/api/v1/skills/{self.python.id}/next-step/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['skill'], 'Django')

    def test_path_to(self):
        response = self.client.get(f'/api/v1/skills/{self.python.id}/path-to/{self.django.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['path'], ['Python', 'Django'])

    def test_progress_update(self):
        response = self.client.post('/api/v1/progress/update/', {'skill_id': self.python.id, 'completion_percent': 80})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['completion_percent'], 80)

    def test_learning_path(self):
        response = self.client.post('/api/v1/learning-path/', {'target_skills': ['Django']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['plan'][0]['target'], 'Django')

    def test_user_path(self):
        response = self.client.get(f'/api/v1/users/{self.user.id}/path/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['current_skills']), 1)
