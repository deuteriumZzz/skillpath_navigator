import logging

from celery.result import AsyncResult
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class IngestSkillsFromTextView(APIView):
    def post(self, request):
        from apps.recommendations.tasks import analyze_skills_text_task
        from django.conf import settings

        text = request.data.get("text", "")
        if not text:
            return Response(
                {"error": "Укажите text"}, status=status.HTTP_400_BAD_REQUEST
            )

        rate_key = f"llm_throttle:{request.user.pk}"
        rate_limit = getattr(settings, "LLM_THROTTLE_RATE_PER_HOUR", 10)
        current = cache.get(rate_key, 0)
        if current >= rate_limit:
            return Response(
                {
                    "error": f"Лимит {rate_limit} запросов в час исчерпан. Попробуйте позже."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        cache.set(rate_key, current + 1, timeout=3600)

        task = analyze_skills_text_task.delay(request.user.pk, text)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        data: dict = {"state": result.state}
        if result.ready():
            if result.successful():
                data["result"] = result.get()
            else:
                data["error"] = str(result.result)
        return Response(data)
