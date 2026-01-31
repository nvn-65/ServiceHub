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

    # Панель управления приёмщика
    path('receiver-dashboard/', views.receiver_dashboard_view, name='receiver_dashboard'),

    # Просмотр деталей акта приёмки
    path('reception-act/<int:act_id>/', views.reception_act_detail, name='reception_act_detail'),

    # Добавляем путь для создания акта приёмки
    path('reception/create/', views.create_reception_act, name='create_reception_act'),

    # Панель управления координатора
    path('coordinator-dashboard/', views.coordinator_dashboard_view, name='coordinator_dashboard'),

    path('electronic/dashboard/', views.electronic_dashboard, name='electronic_dashboard'),
    path('electronic/update-status/', views.update_equipment_status, name='update_equipment_status'),
    path('electronic/add-diagnosis/', views.add_diagnosis, name='add_diagnosis'),
    path('electronic/complete-repair/', views.complete_repair, name='complete_repair'),

    # API для добавления нового клиента
    path('api/add-client/', views.add_client, name='add_client'),

    # API для добавления категории, бренда и модели
    path('api/add-category/', views.add_category, name='add_category'),
    path('api/add-brand/', views.add_brand, name='add_brand'),
    path('api/add-model/', views.add_model, name='add_model'),
    # API для обновления гарантии оборудования
    path('api/update-equipment-guarantee/', views.update_equipment_guarantee, name='update_equipment_guarantee'),
    # API для обновления приоритета и статуса оборудования
    path('api/update-equipment-priority/', views.update_equipment_priority, name='update_equipment_priority'),
    path('api/update-equipment-status/', views.update_equipment_status, name='update_equipment_status'),
]