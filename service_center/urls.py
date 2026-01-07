"""
URL конфигурация для приложения service_center.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('roles/', views.roles_view, name='roles'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]