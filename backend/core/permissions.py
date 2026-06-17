from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """Чтение — любой авторизованный пользователь; запись/удаление — только staff/admin."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """Объект доступен только его владельцу (obj.user) или staff/admin."""

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and (request.user.is_staff or obj.user == request.user)
        )
