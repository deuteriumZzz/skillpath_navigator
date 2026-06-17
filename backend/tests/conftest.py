import pytest


def pytest_configure():
    from django.conf import settings

    if not settings.configured:
        return
    settings.USE_REDIS_CACHE = False
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }


@pytest.fixture(autouse=True)
def reset_cache():
    from django.core.cache import cache

    yield
    cache.clear()
