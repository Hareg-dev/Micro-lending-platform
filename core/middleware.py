from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings
import time


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.rate_window = getattr(settings, 'RATE_LIMIT_WINDOW', 3600)  # 1 hour
    
    def __call__(self, request):
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check rate limit for sensitive endpoints
        if self.is_sensitive_endpoint(request.path):
            if not self.check_rate_limit(ip):
                return HttpResponse("Rate limit exceeded", status=429)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_sensitive_endpoint(self, path):
        sensitive_paths = ['/loans/apply/', '/loans/approve/', '/admin/']
        return any(sensitive in path for sensitive in sensitive_paths)
    
    def check_rate_limit(self, ip):
        cache_key = f'rate_limit_{ip}'
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= self.rate_limit:
            return False
        
        cache.set(cache_key, current_requests + 1, self.rate_window)
        return True