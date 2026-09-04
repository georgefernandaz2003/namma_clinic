class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log mutation requests
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and request.path.startswith('/api/'):
            user = request.user if request.user.is_authenticated else None
            username = user.username if user else 'Anonymous'
            from apps.audit.models import AuditLog
            try:
                AuditLog.objects.create(
                    user=user,
                    username_snapshot=username,
                    action=f"HTTP_{request.method} {request.path[:50]}",
                    details=f"Status: {response.status_code}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except Exception:
                pass
        return response
