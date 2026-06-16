from github import Github
from django.conf import settings
from typing import Optional, List

class ExternalAPI:
    def __init__(self):
        self.github_client = Github(settings.GITHUB_TOKEN)

    def get_github_repos(self, skill: str, limit: int = 5) -> List[dict]:
        """Получает популярные репозитории по навыку"""
        repos = self.github_client.search_repositories(
            f"language:{skill}",
            sort="stars",
            order="desc"
        )
        return [
            {"name": repo.name, "url": repo.html_url, "stars": repo.stargazers_count}
            for repo in repos[:limit]
        ]

    def get_youtube_videos(self, skill: str, limit: int = 3) -> List[dict]:
        """Получает видеоуроки по навыку (мок реализация)"""
        # В реальном проекте использовать YouTube Data API v3
        return [
            {"title": f"{skill} Tutorial {i+1}", "url": f"https://youtube.com/results?search_query={skill}+tutorial"}
            for i in range(limit)
        ]

    def get_courses(self, skill: str) -> Optional[dict]:
        """Получает курсы по навыку (мок)"""
        return {
            "name": f"Ultimate {skill} Course",
            "provider": "Udemy",
            "url": f"https://example.com/courses/{skill}",
            "duration": "10 hours"
        }
