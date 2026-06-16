from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'skills', views.SkillViewSet, basename='skills')
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    path('skills/graph/', views.SkillGraphView.as_view(), name='skill-graph'),
    path('skills/from-text/', views.IngestSkillsFromTextView.as_view(), name='skills-from-text'),
    path('skills/<int:skill_id>/next-step/', views.SkillNextStepView.as_view(), name='skill-next-step'),
    path('skills/<int:skill_id>/resources/', views.SkillResourcesView.as_view(), name='skill-resources'),
    path('skills/<int:from_id>/path-to/<int:to_id>/', views.SkillPathToView.as_view(), name='skill-path-to'),
    path('progress/update/', views.ProgressUpdateView.as_view(), name='progress-update'),
    path('learning-path/', views.LearningPathCreateView.as_view(), name='learning-path'),
    path('users/<int:user_id>/path/', views.UserPathView.as_view(), name='user-path'),
    path('', include(router.urls)),
]
