from github import Github
from django.conf import settings

class GitHubService:
    def __init__(self):
        self.client = Github(settings.GITHUB_TOKEN)

    def search_repos(self, skill_name, limit=5):
        """Поиск репозиториев по навыку"""
        repos = self.client.search_repositories(
            f"language:{skill_name}",
            sort="stars",
            order="desc"
        )
        return [
            {"name": repo.name, "url": repo.html_url, "stars": repo.stargazers_count}
            for repo in repos[:limit]
        ]

    def get_trending_repos(self, limit=5):
        """Популярные репозитории на GitHub"""
        repos = self.client.trending("today", limit=limit)
        return [
            {"name": repo.name, "url": repo.html_url, "stars": repo.stargazers_count}
            for repo in repos
        ]
