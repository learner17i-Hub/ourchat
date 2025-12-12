from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('lobby/', views.lobby_view, name='lobby'),
    path('logout/', views.logout_view, name='logout'),
    path('create_room/', views.create_room_view, name='create_room'),
    path('join_room/', views.join_room_view, name='join_room'),
    path('chat/<str:room_name>/', views.chat_view, name='chat_room'),
    path('api/send_message/', views.send_message_api, name='send_message'),
    path('api/get_messages/', views.get_messages_api, name='get_messages'),
    path('manage/', views.manage_dashboard, name='manage_dashboard'),
    path('manage/<str:room_name>/edit/', views.edit_room, name='edit_room'),
    path('manage/<str:room_name>/members/', views.manage_members, name='manage_members'),
    path('manage/<str:room_name>/kick/<int:user_id>/', views.kick_member, name='kick_member'),
]