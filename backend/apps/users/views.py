from core.pagination import StandardPagination
from rest_framework import generics, permissions, viewsets

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — регистрация нового пользователя. Доступно без авторизации."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.prefetch_related("user_skills__skill").all()
    serializer_class = UserSerializer
    pagination_class = StandardPagination
