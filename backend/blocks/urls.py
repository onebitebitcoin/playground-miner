from django.urls import path
from . import views

urlpatterns = [
    path('status', views.status_view, name='status'),
    path('blocks', views.blocks_view, name='blocks'),
    path('mine', views.mine_view, name='mine'),
    path('stream', views.stream_view, name='stream'),
    path('register_nick', views.register_nick_view, name='register_nick'),
    path('check_nick', views.check_nick_view, name='check_nick'),
    path('init_reset', views.init_reset_view, name='init_reset'),
]
