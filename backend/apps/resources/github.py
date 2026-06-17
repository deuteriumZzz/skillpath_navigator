from typing import Dict, List

import requests
from django.conf import settings


class GitHubService:
    """Поиск репозиториев GitHub по названию навыка. При отсутствии GITHUB_TOKEN
    или при USE_MOCK_EXTERNAL_APIS=True возвращает мок-данные без сетевых запросов.
    """

    BASE_URL = "https://api.github.com/search/repositories"

    def search_repos(self, skill_name: str, limit: int = 5) -> List[Dict]:
        """Популярные репозитории по навыку: реальный GitHub API либо мок без токена."""
        if not skill_name:
            return []

        if settings.USE_MOCK_EXTERNAL_APIS or not settings.GITHUB_TOKEN:
            return self._mock_repos(skill_name, limit)

        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        params = {"q": f"language:{skill_name}", "sort": "stars", "order": "desc", "per_page": limit}

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "name": item.get("name"),
                    "url": item.get("html_url"),
                    "language": item.get("language"),
                    "stars": item.get("stargazers_count"),
                    "description": item.get("description"),
                }
                for item in data.get("items", [])[:limit]
            ]
        except requests.exceptions.RequestException:
            return self._mock_repos(skill_name, limit)

    @staticmethod
    def _mock_repos(skill_name: str, limit: int) -> List[Dict]:
        return [
            {
                "name": f"awesome-{skill_name}-{i + 1}",
                "url": f"https://github.com/search?q=language:{skill_name}",
                "language": skill_name,
                "stars": 1000 - i * 100,
                "description": f"Пример репозитория по теме {skill_name} (мок, GITHUB_TOKEN не задан)",
            }
            for i in range(limit)
        ]
