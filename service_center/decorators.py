"""
Декораторы для проверки прав доступа по ролям.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

from django.shortcuts import redirect

from .models import UserRole


# def role_required(role_name):
#     """
#     Декоратор для проверки наличия у пользователя определённой роли.
#
#     Args:
#         role_name (str): Название требуемой роли
#
#     Returns:
#         function: Декорированная функция
#     """
#
#     def decorator(view_func):
#         @wraps(view_func)
#         @login_required
#         def _wrapped_view(request, *args, **kwargs):
#             # Проверяем, есть ли у пользователя активная роль с указанным именем
#             has_role = UserRole.objects.filter(
#                 user=request.user,
#                 role__name=role_name,
#                 is_active=True
#             ).exists()
#
#             if not has_role:
#                 raise PermissionDenied(
#                     f"Для доступа к этой странице требуется роль '{role_name}'"
#                 )
#
#             return view_func(request, *args, **kwargs)
#
#         return _wrapped_view
#
#     return decorator


def any_role_required(role_names):
    """
    Декоратор для проверки наличия у пользователя хотя бы одной из указанных ролей.

    Args:
        role_names (list): Список названий ролей

    Returns:
        function: Декорированная функция
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Проверяем, есть ли у пользователя хотя бы одна из указанных ролей
            has_role = UserRole.objects.filter(
                user=request.user,
                role__name__in=role_names,
                is_active=True
            ).exists()

            if not has_role:
                role_list = "', '".join(role_names)
                raise PermissionDenied(
                    f"Для доступа к этой странице требуется одна из ролей: '{role_list}'"
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def role_required(role_name):
    """Декоратор для проверки, имеет ли пользователь указанную роль."""

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Проверяем, есть ли у пользователя активная роль
            has_role = UserRole.objects.filter(
                user=request.user,
                role__name=role_name,
                is_active=True
            ).exists()

            if not has_role:
                raise PermissionDenied("У вас нет доступа к этой странице")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator