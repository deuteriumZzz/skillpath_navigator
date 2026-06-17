import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def analyze_skills_text_task(self, user_id: int, text: str) -> dict:
    """Разбирает текстовое описание навыков через LLM и сохраняет их пользователю.

    Возвращает список созданных UserSkill в виде сериализованных данных.
    """
    try:
        from apps.recommendations.services import ingest_skills_from_text
        from apps.skills.serializers import UserSkillSerializer
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(pk=user_id)
        created = ingest_skills_from_text(user, text)
        return {"skills": UserSkillSerializer(created, many=True).data}
    except Exception as exc:
        logger.exception("analyze_skills_text_task failed for user_id=%s", user_id)
        raise self.retry(exc=exc)
