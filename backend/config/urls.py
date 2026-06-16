from django.contrib import admin
from django.urls import include, path
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.api.urls')),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
