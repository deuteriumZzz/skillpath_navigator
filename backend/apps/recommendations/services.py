from typing import List, Optional

from apps.skills.models import Skill, UserSkill

from .llm_analyzer import SkillTextAnalyzer


def ingest_skills_from_text(
    user, text: str, analyzer: Optional[SkillTextAnalyzer] = None
) -> List[UserSkill]:
    """Разбирает свободный текст пользователя в список навыков (через LLM) и сохраняет их."""
    analyzer = analyzer or SkillTextAnalyzer()
    parsed = analyzer.analyze(text)

    created = []
    for item in parsed:
        name = item["name"].strip()
        if not name:
            continue
        level = item.get("level", "beginner")
        skill, _ = Skill.objects.get_or_create(name=name, defaults={"level": level})
        user_skill, _ = UserSkill.objects.update_or_create(
            user=user, skill=skill, defaults={"level": level}
        )
        created.append(user_skill)
    return created
