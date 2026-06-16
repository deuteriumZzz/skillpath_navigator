from typing import Dict, List

import requests
from django.conf import settings


class YouTubeService:
    BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def search_videos(self, skill_name: str, limit: int = 3) -> List[Dict]:
        """Видеоуроки по навыку: реальный YouTube Data API либо мок без ключа."""
        if not skill_name:
            return []

        if settings.USE_MOCK_EXTERNAL_APIS or not settings.YOUTUBE_API_KEY:
            return self._mock_videos(skill_name, limit)

        params = {
            "part": "snippet",
            "q": f"{skill_name} tutorial",
            "type": "video",
            "maxResults": limit,
            "key": settings.YOUTUBE_API_KEY,
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                }
                for item in data.get("items", [])
            ]
        except requests.exceptions.RequestException:
            return self._mock_videos(skill_name, limit)

    @staticmethod
    def _mock_videos(skill_name: str, limit: int) -> List[Dict]:
        return [
            {
                "title": f"{skill_name} Tutorial {i + 1}",
                "url": f"https://www.youtube.com/results?search_query={skill_name}+tutorial",
            }
            for i in range(limit)
        ]
