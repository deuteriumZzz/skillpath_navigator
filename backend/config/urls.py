from django.contrib import admin
from django.urls import include, path

from apps.graphql_schema.views import AuthenticatedGraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.api.urls')),
    path('graphql/', AuthenticatedGraphQLView.as_view(graphiql=True)),
]
