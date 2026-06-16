import requests
from django.conf import settings
from typing import List, Dict
import os
from functools import lru_cache
from urllib.parse import quote

class GitHubService:
    BASE_URL = "https://api.github.com/search/code"

    def __init__(self):
        self.headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}",
            "Accept": "application/vnd.github.v3+json"
        }

    @lru_cache(maxsize=32)
    def search_repos(self, skill_name: str, limit: int = 5) -> List[Dict]:
        """Поиск репозиториев на GitHub по навыку с кэшированием"""
        if not skill_name:
            return []

        query = f"language:{skill_name} in:file"
        params = {
            "q": query,
            "per_page": limit
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            repos = []
            for item in data.get('items', []):
                repo_info = {
                    "name": item.get('repository', {}).get('name'),
                    "url": item.get('repository', {}).get('html_url'),
                    "language": item.get('language'),
                    "stars": item.get('repository', {}).get('stargazers_count'),
                    "description": item.get('description'),
                    "snippet": item.get('text', '').split('\n')[0] if item.get('text') else ''
                }
                repos.append(repo_info)

            return repos[:limit]

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к GitHub: {e}")
            return []
