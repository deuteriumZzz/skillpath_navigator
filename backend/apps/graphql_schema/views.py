from django.http import JsonResponse
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication


class AuthenticatedGraphQLView(GraphQLView):
    """GraphQLView, понимающий тот же JWT, что и REST API (Authorization: Bearer ...)."""

    def dispatch(self, request, *args, **kwargs):
        try:
            result = JWTAuthentication().authenticate(request)
        except Exception:
            result = None

        if result is None:
            return JsonResponse({"error": "Authentication required"}, status=401)

        request.user, _ = result
        return super().dispatch(request, *args, **kwargs)
