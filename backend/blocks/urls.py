from django.urls import path, re_path
from . import views

urlpatterns = [
    path('status', views.status_view, name='status'),
    path('blocks', views.blocks_view, name='blocks'),
    path('mine', views.mine_view, name='mine'),
    path('stream', views.stream_view, name='stream'),
    # Accept both with/without trailing slash
    re_path(r'^register_nick/?$', views.register_nick_view, name='register_nick'),
    re_path(r'^check_nick/?$', views.check_nick_view, name='check_nick'),
    re_path(r'^init_reset/?$', views.init_reset_view, name='init_reset'),
]
