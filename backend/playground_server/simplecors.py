from django.http import HttpResponse


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Preflight 처리
        if request.method == 'OPTIONS':
            resp = HttpResponse(status=200)
            resp['Access-Control-Allow-Origin'] = '*'
            resp['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            resp['Access-Control-Max-Age'] = '600'
            return resp

        response = self.get_response(request)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
