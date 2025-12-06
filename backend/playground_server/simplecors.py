from django.http import HttpResponse
from django.conf import settings


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', ['*'])
        self.allow_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)

    def _get_request_origin(self, request):
        origin = request.headers.get('Origin') or request.META.get('HTTP_ORIGIN')
        if not origin:
            return None
        if '*' in self.allowed_origins:
            return origin
        if origin in self.allowed_origins:
            return origin
        return None

    def _apply_cors_headers(self, response, origin):
        allow_origin_value = None
        if origin:
            allow_origin_value = origin
        elif '*' in self.allowed_origins and not self.allow_credentials:
            allow_origin_value = '*'

        if allow_origin_value:
            response['Access-Control-Allow-Origin'] = allow_origin_value
            if allow_origin_value != '*':
                vary_header = response.get('Vary')
                response['Vary'] = 'Origin' if not vary_header else f"{vary_header}, Origin"
            if self.allow_credentials and allow_origin_value != '*':
                response['Access-Control-Allow-Credentials'] = 'true'

        response['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, PUT, PATCH, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    def __call__(self, request):
        origin = self._get_request_origin(request)

        # Preflight 처리
        if request.method == 'OPTIONS':
            resp = HttpResponse(status=200)
            self._apply_cors_headers(resp, origin)
            resp['Access-Control-Max-Age'] = '600'
            return resp

        response = self.get_response(request)
        self._apply_cors_headers(response, origin)
        return response
