import logging

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resources.course import CoursesService
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


class SkillResourcesView(APIView):
    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, pk=skill_id)
        courses = CoursesService()
        return Response(
            {
                "github_repos": GitHubService().search_repos(skill.name),
                "youtube_videos": YouTubeService().search_videos(skill.name),
                "courses": courses.search_stepik_courses(skill.name)
                + courses.search_coursera_courses(skill.name),
            }
        )
