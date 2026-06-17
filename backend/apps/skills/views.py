import logging

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.graph.services import GraphService
from apps.recommendations.engine import RecommendationEngine
from apps.skills.filters import SkillFilter
from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer
from core.constants import SKILL_GRAPH_CACHE_KEY, SKILL_GRAPH_CACHE_TTL
from core.pagination import StandardPagination
from core.permissions import IsAdminOrReadOnly

logger = logging.getLogger(__name__)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = SkillFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "level", "created_at"]
    ordering = ["name"]


class SkillGraphView(APIView):
    def get(self, request):
        payload = cache.get(SKILL_GRAPH_CACHE_KEY)
        if payload is None:
            payload = GraphService().to_graph_payload()
            cache.set(SKILL_GRAPH_CACHE_KEY, payload, SKILL_GRAPH_CACHE_TTL)
        return Response(payload)


class SkillNextStepView(APIView):
    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, pk=skill_id)
        recommendations = RecommendationEngine().get_next_skills([skill.name])
        return Response(recommendations)


class SkillPathToView(APIView):
    def get(self, request, from_id, to_id):
        start = get_object_or_404(Skill, pk=from_id)
        end = get_object_or_404(Skill, pk=to_id)
        path = GraphService().find_shortest_path(start.name, end.name)
        if path is None:
            return Response(
                {"error": "Путь не найден"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(path)
