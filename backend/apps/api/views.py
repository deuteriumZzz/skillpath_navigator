from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.cache import cache

from core.constants import SKILL_GRAPH_CACHE_KEY, SKILL_GRAPH_CACHE_TTL
from core.pagination import StandardPagination
from core.permissions import IsAdminOrReadOnly
from apps.skills.filters import SkillFilter
from apps.graph.services import GraphService
from apps.progress.models import UserSkillProgress
from apps.progress.serializers import ProgressUpdateSerializer, UserSkillProgressSerializer
from apps.progress.services import broadcast_progress_update
from apps.recommendations.engine import RecommendationEngine
from apps.recommendations.services import ingest_skills_from_text
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

        progress, _ = UserSkillProgress.objects.update_or_create(
            user=request.user, skill=skill, defaults={'completion_percent': percent}
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
    """POST /api/skills/from-text/ — разобрать текстовое описание навыков пользователя через LLM."""

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({"error": "Укажите text"}, status=status.HTTP_400_BAD_REQUEST)
        created = ingest_skills_from_text(request.user, text)
        return Response(UserSkillSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class HealthCheckView(APIView):
    """GET /api/v1/health/ — liveness probe для Docker/k8s."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})
