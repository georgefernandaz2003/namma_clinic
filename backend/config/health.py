"""
Health and readiness probe endpoints for orchestrators (Docker, Kubernetes, AWS ECS).
Unauthenticated, lightweight, fast, and does not leak database credentials or internals.
"""
import logging
from django.http import JsonResponse
from django.db import connection

logger = logging.getLogger('apps.health')


def healthz(request):
    """
    Liveness probe: Confirms that the Django WSGI process is alive and responding.
    Returns HTTP 200 with {"status": "ok"}.
    """
    return JsonResponse({"status": "ok"}, status=200)


def readyz(request):
    """
    Readiness probe: Confirms that the application process can communicate with
    the backend database. Does not expose credentials, hosts, or sensitive internal state.
    Returns HTTP 200 when ready, or HTTP 503 when dependencies are unavailable.
    """
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return JsonResponse({"status": "ready", "database": "connected"}, status=200)
    except Exception as exc:
        logger.error("Readiness check failed: %s: %s", exc.__class__.__name__, str(exc))
        return JsonResponse({"status": "not ready", "database": "unavailable"}, status=503)
