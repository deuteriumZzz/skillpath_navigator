import logging

from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """GET /api/v1/health/ — liveness probe."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ReadinessCheckView(APIView):
    """GET /api/v1/ready/ — readiness probe: проверяет DB и Redis."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        checks: dict = {}
        overall = True

        try:
            connection.ensure_connection()
            checks["db"] = "ok"
        except Exception:
            checks["db"] = "error"
            overall = False

        try:
            cache.set("_readiness_ping", "1", timeout=5)
            checks["cache"] = "ok"
        except Exception:
            checks["cache"] = "error"
            overall = False

        http_status = status.HTTP_200_OK if overall else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({"status": "ok" if overall else "degraded", "checks": checks}, status=http_status)
