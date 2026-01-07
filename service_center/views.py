"""
Представления для приложения ServiceHub.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import UserRole


def login_view(request):
    """
    Представление для входа пользователя.
    """
    if request.user.is_authenticated:
        return redirect('roles')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('roles')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()

    return render(request, 'service_center/login.html', {'form': form})


@login_required
def roles_view(request):
    """
    Представление для отображения доступных ролей пользователя.
    """
    user_roles = UserRole.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('role')

    context = {
        'user_roles': user_roles,
    }

    return render(request, 'service_center/roles.html', context)


def home_view(request):
    """
    Домашняя страница.
    """
    if request.user.is_authenticated:
        return redirect('roles')

    return render(request, 'service_center/home.html')