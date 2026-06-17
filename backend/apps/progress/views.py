import logging

from apps.progress.models import UserSkillProgress
from apps.progress.serializers import (
    ProgressUpdateSerializer,
    UserSkillProgressSerializer,
)
from apps.progress.services import broadcast_progress_update
from apps.recommendations.engine import RecommendationEngine
from apps.skills.models import UserSkill
from apps.skills.serializers import UserSkillSerializer
from apps.users.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

_MAX_TARGET_SKILLS = 10


class ProgressUpdateView(APIView):
    def post(self, request):
        serializer = ProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skill = serializer.validated_data["skill_id"]
        percent = serializer.validated_data["completion_percent"]

        with transaction.atomic():
            try:
                progress = UserSkillProgress.objects.select_for_update().get(
                    user=request.user, skill=skill
                )
                progress.completion_percent = percent
                progress.save(update_fields=["completion_percent"])
            except UserSkillProgress.DoesNotExist:
                progress = UserSkillProgress.objects.create(
                    user=request.user, skill=skill, completion_percent=percent
                )

        broadcast_progress_update(
            request.user.id, skill.name, progress.completion_percent
        )
        return Response(UserSkillProgressSerializer(progress).data)


class LearningPathCreateView(APIView):
    def post(self, request):
        target_skills = request.data.get("target_skills", [])
        if not target_skills:
            return Response(
                {"error": "Укажите target_skills"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(target_skills) > _MAX_TARGET_SKILLS:
            return Response(
                {
                    "error": f"Нельзя указывать более {_MAX_TARGET_SKILLS} целевых навыков за один запрос."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        engine = RecommendationEngine()
        known = list(request.user.user_skills.values_list("skill__name", flat=True))
        candidate_starts = known or engine.graph.find_skills_by_level("beginner")
        candidate_starts = candidate_starts[:20]

        plan = []
        for target in target_skills:
            best_path = None
            for start_skill in candidate_starts:
                path = engine.find_learning_path(start_skill, target)
                if path and (
                    best_path is None or path["distance"] < best_path["distance"]
                ):
                    best_path = path
            plan.append({"target": target, "path": best_path})
        return Response({"plan": plan})


class UserPathView(APIView):
    def get(self, request, user_id):
        if not request.user.is_staff and request.user.pk != user_id:
            return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=user_id)
        skills = UserSkill.objects.filter(user=user).select_related("skill")
        progress = UserSkillProgress.objects.filter(user=user).select_related("skill")
        return Response(
            {
                "current_skills": UserSkillSerializer(skills, many=True).data,
                "progress": UserSkillProgressSerializer(progress, many=True).data,
            }
        )
