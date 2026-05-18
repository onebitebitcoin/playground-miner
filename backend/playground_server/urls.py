import os
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.urls import path, include, re_path


def health_check(request):
    return JsonResponse({'status': 'ok'})


def spa_view(request, path=''):
    index_path = os.path.join(settings.BASE_DIR, 'frontend_dist', 'index.html')
    with open(index_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='text/html; charset=utf-8')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/', include('blocks.urls')),
    re_path(r'^.*$', spa_view),
]

