import requests
from django.conf import settings
import os

class CoursesService:
    def __init__(self):
        self.stepik_token = os.getenv('STEPIK_TOKEN')
        self.coursera_token = os.getenv('COURSERA_TOKEN')

    def search_stepik_courses(self, skill_name, limit=3):
        """Поиск курсов на Stepik по навыку"""
        url = "https://stepik.org/api/courses/"
        headers = {"Authorization": f"Token {self.stepik_token}"}

        # Пример запроса (мок): в реальности нужно использовать API Stepik
        response = requests.get(
            url,
            headers=headers,
            params={"q": skill_name},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "title": course.get("title", ""),
                    "url": f"https://stepik.org/course/{course.get('id', '')}",
                    "lessons_count": course.get("lessons_count", 0)
                }
                for course in data[:limit]
            ]
        return []

    def search_coursera_courses(self, skill_name, limit=3):
        """Поиск курсов на Coursera по навыку (мок)"""
        # В реальности нужно использовать официальный API Coursera
        mock_courses = [
            {
                "title": f"Обучение {skill_name} на Coursera",
                "url": f"https://www.coursera.org/courses?query={skill_name}",
                "rating": 4.5
            }
            for _ in range(limit)
        ]
        return mock_courses
