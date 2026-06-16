"""
ASGI config for skillpath_navigator project.
Обслуживает и обычные HTTP-запросы (Django/DRF/GraphQL), и WebSocket (Channels) — обновления прогресса.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django ASGI-приложение должно быть создано до импорта модулей, использующих модели.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.progress.routing import websocket_urlpatterns  # noqa: E402
from core.middleware import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
