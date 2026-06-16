import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ProgressConsumer(AsyncWebsocketConsumer):
    """Транслирует обновления прогресса пользователю в реальном времени.

    Подключение: ws://.../ws/progress/<user_id>/?token=<access_token>
    Сервер рассылает событие при каждом POST /api/progress/update/ (см. apps.progress.services.broadcast_progress_update).
    """

    async def connect(self):
        user = self.scope.get("user")
        target_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if not user.is_staff and user.pk != target_user_id:
            await self.close(code=4003)
            return

        self.user_id = target_user_id
        self.group_name = f"progress_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def progress_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
