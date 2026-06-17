from typing import Dict, List

import requests
from django.conf import settings


class CoursesService:
    """Поиск онлайн-курсов по навыку на Stepik и Coursera. Stepik использует реальный API
    при наличии STEPIK_TOKEN; Coursera всегда возвращает мок (публичный API недоступен без
    партнёрского доступа). USE_MOCK_EXTERNAL_APIS=True форсирует мок для обоих провайдеров.
    """

    STEPIK_URL = "https://stepik.org/api/courses/"

    def search_stepik_courses(self, skill_name: str, limit: int = 3) -> List[Dict]:
        """Курсы Stepik по навыку: реальный API либо мок при отсутствии STEPIK_TOKEN."""
        if not skill_name:
            return []

        if settings.USE_MOCK_EXTERNAL_APIS or not settings.STEPIK_TOKEN:
            return self._mock_courses(skill_name, limit, provider="Stepik")

        headers = {"Authorization": f"Token {settings.STEPIK_TOKEN}"}
        try:
            response = requests.get(
                self.STEPIK_URL, headers=headers, params={"q": skill_name}, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": course.get("title", ""),
                    "url": f"https://stepik.org/course/{course.get('id', '')}",
                    "lessons_count": course.get("lessons_count", 0),
                }
                for course in data.get("courses", [])[:limit]
            ]
        except requests.exceptions.RequestException:
            return self._mock_courses(skill_name, limit, provider="Stepik")

    def search_coursera_courses(self, skill_name: str, limit: int = 3) -> List[Dict]:
        """Курсы Coursera по навыку: всегда возвращает мок (публичного API поиска нет)."""
        if not skill_name:
            return []
        # Официального публичного поиска курсов Coursera без партнёрского доступа нет — всегда мок.
        return self._mock_courses(skill_name, limit, provider="Coursera")

    @staticmethod
    def _mock_courses(skill_name: str, limit: int, provider: str) -> List[Dict]:
        return [
            {
                "title": f"Обучение «{skill_name}» на {provider} (курс {i + 1})",
                "url": f"https://www.google.com/search?q={provider}+{skill_name}+course",
                "lessons_count": 10 + i,
                "rating": 4.5,
            }
            for i in range(limit)
        ]
