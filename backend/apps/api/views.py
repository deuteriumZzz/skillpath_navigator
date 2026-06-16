from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer
from apps.recommendations.engine import RecommendationEngine
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from apps.users.models import User
from apps.users.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        skill_serializer = self.get_serializer(data=request.data)
        if skill_serializer.is_valid():
            skill = skill_serializer.save(owner=request.user)

            # Автоматический анализ уровня навыка
            engine = RecommendationEngine()
            analysis = engine.analyze_skill(skill.description)
            skill.level = analysis["level"]
            skill.save()

            return Response(skill_serializer.data, status=status.HTTP_201_CREATED)
        return Response(skill_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def recommend_next(self, request, pk=None):
        skill = self.get_object()
        engine = RecommendationEngine()
        recommendations = engine.get_next_skills([skill])
        return Response(recommendations)

class RecommendationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def next_skills(self, request):
        skills = request.user.skills.all()
        engine = RecommendationEngine()
        recommendations = engine.get_next_skills(skills)
        return Response(recommendations)

    @action(detail=False, methods=['get'])
    def learning_path(self, request):
        start_skill = request.GET.get('start')
        end_skill = request.GET.get('end')

        if not start_skill or not end_skill:
            return Response(
                {"error": "Укажите параметры start и end"},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = RecommendationEngine()
        path = engine.find_learning_path(start_skill, end_skill)
        return Response({"path": path} if path else {"error": "Путь не найден"})

class ResourcesViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def github_repos(self, request):
        skill_name = request.GET.get('skill')
        if not skill_name:
            return Response(
                {"error": "Укажите параметр skill"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = GitHubService()
        repos = service.search_repos(skill_name)
        return Response({"repos": repos})

    @action(detail=False, methods=['get'])
    def youtube_videos(self, request):
        skill_name = request.GET.get('skill')
        if not skill_name:
            return Response(
                {"error": "Укажите параметр skill"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = YouTubeService()
        videos = service.search_videos(skill_name)
        return Response({"videos": videos})
