from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.views import HealthCheckView, ReadinessCheckView
from apps.progress.views import LearningPathCreateView, ProgressUpdateView, UserPathView
from apps.recommendations.views import IngestSkillsFromTextView, TaskStatusView
from apps.resources.views import SkillResourcesView
from apps.skills.views import (
    SkillGraphView,
    SkillNextStepView,
    SkillPathToView,
    SkillViewSet,
)
from apps.users.views import UserViewSet

router = DefaultRouter()
router.register(r"skills", SkillViewSet, basename="skills")
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("ready/", ReadinessCheckView.as_view(), name="ready"),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
    path("skills/graph/", SkillGraphView.as_view(), name="skill-graph"),
    path(
        "skills/from-text/", IngestSkillsFromTextView.as_view(), name="skills-from-text"
    ),
    path(
        "skills/<int:skill_id>/next-step/",
        SkillNextStepView.as_view(),
        name="skill-next-step",
    ),
    path(
        "skills/<int:skill_id>/resources/",
        SkillResourcesView.as_view(),
        name="skill-resources",
    ),
    path(
        "skills/<int:from_id>/path-to/<int:to_id>/",
        SkillPathToView.as_view(),
        name="skill-path-to",
    ),
    path("progress/update/", ProgressUpdateView.as_view(), name="progress-update"),
    path("learning-path/", LearningPathCreateView.as_view(), name="learning-path"),
    path("users/<int:user_id>/path/", UserPathView.as_view(), name="user-path"),
    path("", include(router.urls)),
]
