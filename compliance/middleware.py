from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log sensitive operations
        if request.method in ['POST', 'PUT', 'DELETE'] and request.user.is_authenticated:
            if any(path in request.path for path in ['/loans/', '/admin/']):
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    details={'path': request.path, 'method': request.method},
                    ip_address=self.get_client_ip(request)
                )
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip