from apps.resources.course import CoursesService
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from django.test import TestCase


class MockExternalApisTestCase(TestCase):
    """По умолчанию settings.USE_MOCK_EXTERNAL_APIS=True — реальные сетевые вызовы не выполняются."""

    def test_github_mock(self):
        repos = GitHubService().search_repos("Python", limit=2)
        self.assertEqual(len(repos), 2)
        self.assertIn("Python", repos[0]["name"])

    def test_youtube_mock(self):
        videos = YouTubeService().search_videos("Python", limit=2)
        self.assertEqual(len(videos), 2)
        self.assertIn("Python", videos[0]["title"])

    def test_courses_mock(self):
        courses = CoursesService().search_stepik_courses("Python", limit=2)
        self.assertEqual(len(courses), 2)

    def test_empty_skill_name_returns_empty(self):
        self.assertEqual(GitHubService().search_repos(""), [])
        self.assertEqual(YouTubeService().search_videos(""), [])
