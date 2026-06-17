from apps.skills.models import Skill
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class SkillPermissionsTestCase(APITestCase):
    """IsAdminOrReadOnly: обычный пользователь читает, но не пишет."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@ex.com", password="pass12345"
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@ex.com", password="pass12345", is_staff=True
        )
        self.skill = Skill.objects.create(name="Python", level="beginner")

    def test_regular_user_can_list_skills(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/skills/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_skill(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/v1/skills/", {"name": "Go", "level": "beginner"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_skill(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/v1/skills/{self.skill.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_skill(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/skills/", {"name": "Rust", "level": "advanced"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get("/api/v1/skills/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPathPermissionsTestCase(APITestCase):
    """Пользователь видит только свой путь."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="bob", email="bob@ex.com", password="pass12345"
        )
        self.other = User.objects.create_user(
            username="eve", email="eve@ex.com", password="pass12345"
        )
        self.admin = User.objects.create_user(
            username="root", email="root@ex.com", password="pass12345", is_staff=True
        )

    def test_user_can_view_own_path(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/users/{self.user.id}/path/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_view_other_path(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/users/{self.other.id}/path/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_path(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/v1/users/{self.user.id}/path/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaginationTestCase(APITestCase):
    """Листинг возвращает пагинированный ответ."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="carol", email="carol@ex.com", password="pass12345"
        )
        self.client.force_authenticate(self.user)
        for i in range(5):
            Skill.objects.create(name=f"Skill {i}", level="beginner")

    def test_skills_list_is_paginated(self):
        response = self.client.get("/api/v1/skills/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIn("next", response.data)

    def test_page_size_param(self):
        response = self.client.get("/api/v1/skills/?page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["results"]), 2)


class SkillFilterTestCase(APITestCase):
    """Фильтрация навыков по уровню и имени."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="dave", email="dave@ex.com", password="pass12345"
        )
        self.client.force_authenticate(self.user)
        Skill.objects.create(name="Python", level="beginner")
        Skill.objects.create(name="Django", level="intermediate")
        Skill.objects.create(name="Kubernetes", level="advanced")

    def test_filter_by_level(self):
        response = self.client.get("/api/v1/skills/?level=beginner")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Python")

    def test_search_by_name(self):
        response = self.client.get("/api/v1/skills/?search=djan")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Django")
