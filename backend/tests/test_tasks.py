from unittest.mock import patch

import pytest
from django.test import TestCase
from rest_framework.test import APIClient

from tests.factories import SkillFactory, UserFactory


@pytest.mark.django_db
class TaskStatusViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    @patch("apps.api.views_recommendations.AsyncResult")
    def test_pending_task(self, mock_result_cls):
        mock_result_cls.return_value.state = "PENDING"
        mock_result_cls.return_value.ready.return_value = False

        res = self.client.get("/api/v1/tasks/fake-task-id/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["state"], "PENDING")

    @patch("apps.api.views_recommendations.AsyncResult")
    def test_successful_task(self, mock_result_cls):
        mock_result_cls.return_value.state = "SUCCESS"
        mock_result_cls.return_value.ready.return_value = True
        mock_result_cls.return_value.successful.return_value = True
        mock_result_cls.return_value.get.return_value = {"skills": []}

        res = self.client.get("/api/v1/tasks/fake-task-id/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["result"], {"skills": []})


@pytest.mark.django_db
class IngestRateLimitTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    @patch("apps.recommendations.tasks.analyze_skills_text_task")
    def test_rate_limit_enforced(self, mock_task):
        mock_task.delay.return_value.id = "task-123"

        from django.conf import settings
        from django.core.cache import cache

        rate_key = f"llm_throttle:{self.user.pk}"
        limit = getattr(settings, "LLM_THROTTLE_RATE_PER_HOUR", 10)
        cache.set(rate_key, limit, timeout=3600)

        res = self.client.post(
            "/api/v1/skills/from-text/", {"text": "Python developer"}, format="json"
        )
        self.assertEqual(res.status_code, 429)

    @patch("apps.recommendations.tasks.analyze_skills_text_task")
    def test_task_dispatched(self, mock_task):
        mock_task.delay.return_value.id = "task-abc"

        res = self.client.post(
            "/api/v1/skills/from-text/", {"text": "Django REST expert"}, format="json"
        )

        self.assertEqual(res.status_code, 202)
        self.assertIn("task_id", res.json())


@pytest.mark.django_db
class ProgressUpdateConcurrencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.skill = SkillFactory()
        self.client.force_authenticate(user=self.user)

    def test_progress_created_on_first_update(self):
        res = self.client.post(
            "/api/v1/progress/update/",
            {"skill_id": self.skill.pk, "completion_percent": 50},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["completion_percent"], 50)

    def test_progress_updated_on_second_call(self):
        self.client.post(
            "/api/v1/progress/update/",
            {"skill_id": self.skill.pk, "completion_percent": 30},
            format="json",
        )
        res = self.client.post(
            "/api/v1/progress/update/",
            {"skill_id": self.skill.pk, "completion_percent": 75},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["completion_percent"], 75)
