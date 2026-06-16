from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication


class AuthenticatedGraphQLView(GraphQLView):
    """GraphQLView, понимающий тот же JWT, что и REST API (Authorization: Bearer ...)."""

    def dispatch(self, request, *args, **kwargs):
        try:
            result = JWTAuthentication().authenticate(request)
        except Exception:
            result = None
        if result is not None:
            request.user, _ = result
        return super().dispatch(request, *args, **kwargs)
