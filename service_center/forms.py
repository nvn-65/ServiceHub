"""
Формы для приложения ServiceHub.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма создания пользователя с упрощённой валидацией пароля.
    """

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем email обязательным
        self.fields['email'].required = True

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        # Минимальная длина 4 символа
        if len(password1) < 4:
            raise forms.ValidationError(
                'Пароль должен содержать минимум 4 символа.'
            )
        return password1