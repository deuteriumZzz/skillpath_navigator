"""Заполняет граф навыков стартовым набором. Запуск: python backend/scripts/init_neo4j_graph.py"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.graph.services import add_dependency, add_skill_to_graph  # noqa: E402


def load_knowledge_graph():
    """Загружает начальные зависимости между навыками"""
    base_skills = {
        "Python": "beginner",
        "HTML": "beginner",
        "CSS": "beginner",
        "JavaScript": "intermediate",
        "Flask": "intermediate",
        "Django": "advanced",
        "Neo4j": "advanced",
        "SQL": "beginner",
        "Git": "beginner",
        "Docker": "advanced",
    }

    dependencies = {
        "Python": ["SQL", "Git"],
        "HTML": ["CSS"],
        "CSS": ["JavaScript"],
        "JavaScript": ["HTML", "CSS"],
        "Flask": ["Python"],
        "Django": ["Python", "SQL"],
        "Neo4j": ["SQL"],
        "Docker": ["Git"],
    }

    # Добавляем навыки
    for skill, level in base_skills.items():
        add_skill_to_graph(skill, level)

    # Добавляем зависимости
    for skill, deps in dependencies.items():
        for dep in deps:
            add_dependency(skill, dep)


if __name__ == "__main__":
    load_knowledge_graph()
    print("Граф зависимостей между навыками успешно загружен!")
