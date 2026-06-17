import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def broadcast_progress_update(
    user_id: int, skill_name: str, completion_percent: int
) -> None:
    """Отправляет обновление прогресса всем активным WebSocket-подключениям пользователя.

    Это лучшее-из-возможных уведомление, а не основная бизнес-операция: если Redis/channel
    layer недоступен, обновление прогресса в БД всё равно должно считаться успешным.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            f"progress_{user_id}",
            {
                "type": "progress_update",
                "data": {"skill": skill_name, "completion_percent": completion_percent},
            },
        )
    except Exception:
        logger.warning(
            "Не удалось отправить WebSocket-уведомление о прогрессе", exc_info=True
        )
