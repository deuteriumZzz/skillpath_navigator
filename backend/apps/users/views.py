from rest_framework import generics, permissions

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — регистрация нового пользователя. Доступно без авторизации."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
