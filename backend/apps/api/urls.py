from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    SkillViewSet,
    RecommendationViewSet,
    ResourcesViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'recommendations', RecommendationViewSet, basename='recommendations')
router.register(r'resources', ResourcesViewSet, basename='resources')

urlpatterns = [
    path('', include(router.urls)),
]
