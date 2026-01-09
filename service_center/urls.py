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

    # Добавляем путь для создания акта приёмки
    path('reception/create/', views.create_reception_act, name='create_reception_act'),

    # API для добавления нового клиента
    path('api/add-client/', views.add_client, name='add_client'),

    # API для добавления категории, бренда и модели
    path('api/add-category/', views.add_category, name='add_category'),
    path('api/add-brand/', views.add_brand, name='add_brand'),
    path('api/add-model/', views.add_model, name='add_model'),
]