import logging

from django.core.cache import cache
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from core.constants import SKILL_GRAPH_CACHE_KEY, SKILL_GRAPH_CACHE_TTL
from core.pagination import StandardPagination
from core.permissions import IsAdminOrReadOnly
from apps.skills.filters import SkillFilter
from apps.graph.services import GraphService
from apps.progress.models import UserSkillProgress
from apps.progress.serializers import ProgressUpdateSerializer, UserSkillProgressSerializer
from apps.progress.services import broadcast_progress_update
from apps.recommendations.engine import RecommendationEngine
from apps.resources.course import CoursesService
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from apps.skills.models import Skill, UserSkill
from apps.skills.serializers import SkillSerializer, UserSkillSerializer
from apps.users.models import User
from apps.users.serializers import UserSerializer


class SkillViewSet(viewsets.ModelViewSet):
    """CRUD-набор для навыков с поддержкой фильтрации, поиска и сортировки."""

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = SkillFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "level", "created_at"]
    ordering = ["name"]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only набор для пользователей с предзагрузкой их навыков."""

    queryset = User.objects.prefetch_related("user_skills__skill").all()
    serializer_class = UserSerializer
    pagination_class = StandardPagination


class SkillGraphView(APIView):
    """GET /api/skills/graph/ — узлы и зависимости графа."""

    def get(self, request):
        payload = cache.get(SKILL_GRAPH_CACHE_KEY)
        if payload is None:
            payload = GraphService().to_graph_payload()
            cache.set(SKILL_GRAPH_CACHE_KEY, payload, SKILL_GRAPH_CACHE_TTL)
        return Response(payload)


class SkillNextStepView(APIView):
    """GET /api/skills/{id}/next-step/ — рекомендованные следующие навыки. Input: skill_id."""

    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, pk=skill_id)
        recommendations = RecommendationEngine().get_next_skills([skill.name])
        return Response(recommendations)


class SkillPathToView(APIView):
    """GET /api/skills/{from}/path-to/{to}/ — кратчайший путь обучения между навыками."""

    def get(self, request, from_id, to_id):
        start = get_object_or_404(Skill, pk=from_id)
        end = get_object_or_404(Skill, pk=to_id)
        path = GraphService().find_shortest_path(start.name, end.name)
        if path is None:
            return Response({"error": "Путь не найден"}, status=status.HTTP_404_NOT_FOUND)
        return Response(path)


class SkillResourcesView(APIView):
    """GET /api/skills/{id}/resources/ — где искать материалы по навыку."""

    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, pk=skill_id)
        courses = CoursesService()
        return Response({
            "github_repos": GitHubService().search_repos(skill.name),
            "youtube_videos": YouTubeService().search_videos(skill.name),
            "courses": courses.search_stepik_courses(skill.name) + courses.search_coursera_courses(skill.name),
        })


class ProgressUpdateView(APIView):
    """POST /api/progress/update/ — обновить прогресс. Input: skill_id, completion_percent."""

    def post(self, request):
        serializer = ProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skill = serializer.validated_data['skill_id']
        percent = serializer.validated_data['completion_percent']

        with transaction.atomic():
            try:
                progress = UserSkillProgress.objects.select_for_update().get(
                    user=request.user, skill=skill
                )
                progress.completion_percent = percent
                progress.save(update_fields=['completion_percent'])
            except UserSkillProgress.DoesNotExist:
                progress = UserSkillProgress.objects.create(
                    user=request.user, skill=skill, completion_percent=percent
                )

        broadcast_progress_update(request.user.id, skill.name, progress.completion_percent)
        return Response(UserSkillProgressSerializer(progress).data)


class LearningPathCreateView(APIView):
    """POST /api/learning-path/ — оптимизированный план обучения. Input: target_skills (массив имён навыков)."""

    def post(self, request):
        target_skills = request.data.get('target_skills', [])
        if not target_skills:
            return Response({"error": "Укажите target_skills"}, status=status.HTTP_400_BAD_REQUEST)

        engine = RecommendationEngine()
        known = list(request.user.user_skills.values_list('skill__name', flat=True))
        candidate_starts = known or engine.graph.find_skills_by_level('beginner')

        plan = []
        for target in target_skills:
            best_path = None
            for start_skill in candidate_starts:
                path = engine.find_learning_path(start_skill, target)
                if path and (best_path is None or path['distance'] < best_path['distance']):
                    best_path = path
            plan.append({"target": target, "path": best_path})
        return Response({"plan": plan})


class UserPathView(APIView):
    """GET /api/users/{id}/path/ — текущий путь пользователя и прогресс."""

    def get(self, request, user_id):
        if not request.user.is_staff and request.user.pk != user_id:
            return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=user_id)
        skills = UserSkill.objects.filter(user=user).select_related('skill')
        progress = UserSkillProgress.objects.filter(user=user).select_related('skill')
        return Response({
            "current_skills": UserSkillSerializer(skills, many=True).data,
            "progress": UserSkillProgressSerializer(progress, many=True).data,
        })


class IngestSkillsFromTextView(APIView):
    """POST /api/skills/from-text/ — отправляет текст на LLM-анализ через Celery.

    Возвращает {task_id} для последующего опроса GET /api/v1/tasks/{task_id}/.
    Лимит: LLM_THROTTLE_RATE_PER_HOUR запросов на пользователя в час.
    """

    def post(self, request):
        from django.conf import settings
        from apps.recommendations.tasks import analyze_skills_text_task

        text = request.data.get('text', '')
        if not text:
            return Response({"error": "Укажите text"}, status=status.HTTP_400_BAD_REQUEST)

        rate_key = f"llm_throttle:{request.user.pk}"
        rate_limit = getattr(settings, "LLM_THROTTLE_RATE_PER_HOUR", 10)
        current = cache.get(rate_key, 0)
        if current >= rate_limit:
            return Response(
                {"error": f"Лимит {rate_limit} запросов в час исчерпан. Попробуйте позже."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        cache.set(rate_key, current + 1, timeout=3600)

        task = analyze_skills_text_task.delay(request.user.pk, text)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """GET /api/v1/tasks/{task_id}/ — статус Celery-задачи.

    Возвращает {state, result} после завершения анализа навыков.
    """

    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        data: dict = {"state": result.state}
        if result.ready():
            if result.successful():
                data["result"] = result.get()
            else:
                data["error"] = str(result.result)
        return Response(data)


class HealthCheckView(APIView):
    """GET /api/v1/health/ — liveness probe для Docker/k8s."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ReadinessCheckView(APIView):
    """GET /api/v1/ready/ — readiness probe: проверяет DB и Redis."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        checks: dict = {}
        overall = True

        try:
            connection.ensure_connection()
            checks["db"] = "ok"
        except Exception:
            checks["db"] = "error"
            overall = False

        try:
            cache.set("_readiness_ping", "1", timeout=5)
            checks["cache"] = "ok"
        except Exception:
            checks["cache"] = "error"
            overall = False

        http_status = status.HTTP_200_OK if overall else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({"status": "ok" if overall else "degraded", "checks": checks}, status=http_status)
