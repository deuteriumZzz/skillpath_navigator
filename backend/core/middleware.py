from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(user_id: int):
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Извлекает JWT из query-параметра ?token=<jwt> и устанавливает scope['user'].

    Использование на клиенте: ws://host/ws/progress/1/?token=<access_token>
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        scope["user"] = AnonymousUser()
        if token_list:
            try:
                token = AccessToken(token_list[0])
                scope["user"] = await _get_user(token["user_id"])
            except (InvalidToken, TokenError, KeyError):
                pass

        return await super().__call__(scope, receive, send)
