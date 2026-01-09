"""
Представления для приложения ServiceHub.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.db.models import Max
from .models import UserRole, Client, EquipmentCategory, Brand, EquipmentModel, ReceptionAct, ReceivedEquipment
import json
from datetime import datetime


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


def generate_act_number():
    """
    Генерация номера акта в формате DDMMYYYY-XXXX.
    Где XXXX - последовательный номер акта в текущем году, начиная с 0001.
    """
    from django.utils import timezone
    from .models import ReceptionAct

    now = timezone.now()
    current_year = now.year
    date_str = now.strftime('%d%m%Y')

    # Ищем максимальный порядковый номер среди актов текущего года
    acts_this_year = ReceptionAct.objects.filter(
        created_at__year=current_year
    )

    max_serial = 0
    for act in acts_this_year:
        # Парсим номер акта: DDMMYYYY-XXXX
        try:
            parts = act.act_number.split('-')
            if len(parts) == 2:
                serial_part = parts[1]
                serial_num = int(serial_part)
                if serial_num > max_serial:
                    max_serial = serial_num
        except (ValueError, IndexError):
            continue

    new_serial = max_serial + 1

    return f"{date_str}-{new_serial:04d}"


@login_required
def create_reception_act(request):
    """
    Страница для создания акта приёмки оборудования.
    """
    # Проверяем, есть ли у пользователя роль Приёмщик
    has_receiver_role = UserRole.objects.filter(
        user=request.user,
        role__name='Приёмщик',
        is_active=True
    ).exists()

    if not has_receiver_role:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('roles')

    # Генерация номера акта
    act_number = generate_act_number()

    # Получаем данные для формы
    clients = Client.objects.all().order_by('short_name')
    categories = EquipmentCategory.objects.all().order_by('name')

    # Подготавливаем данные для зависимых списков
    brands_by_category = {}
    models_by_brand = {}

    for category in categories:
        brands_by_category[category.id] = list(
            category.brands.all().order_by('name').values('id', 'name')
        )

    all_brands = Brand.objects.all().select_related('category')
    for brand in all_brands:
        models_by_brand[brand.id] = list(
            brand.models.all().order_by('name').values('id', 'name')
        )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Получаем данные из формы
                data = request.POST

                # Обработка клиента
                client_id = data.get('client_id')
                if client_id:
                    client = Client.objects.get(id=client_id)
                    # Обновляем поля клиента
                    client.contact_person = data.get('contact_person', '')
                    client.phone = data.get('phone', '')
                    client.email = data.get('email', '')
                    client.save()
                else:
                    raise ValueError("Клиент не выбран")

                # Создаем акт приёмки
                act = ReceptionAct.objects.create(
                    act_number=act_number,
                    client=client,
                    receiver=request.user,
                    guarantee_type='NONE'
                )

                # Обработка оборудования
                equipment_count = int(data.get('equipment_count', 0))
                equipment_saved = False

                for i in range(equipment_count):
                    category_id = data.get(f'equipment_{i}_category')
                    brand_id = data.get(f'equipment_{i}_brand')
                    model_id = data.get(f'equipment_{i}_model')
                    serial_number = data.get(f'equipment_{i}_serial_number', 'Без номера')
                    inventory_number = data.get(f'equipment_{i}_inventory_number', '')
                    guarantee_type = data.get(f'equipment_{i}_guarantee', 'NONE')
                    defect_description = data.get(f'equipment_{i}_defect_description', '')

                    if model_id:
                        equipment_model = EquipmentModel.objects.get(id=model_id)

                        ReceivedEquipment.objects.create(
                            reception_act=act,
                            model=equipment_model,
                            serial_number=serial_number,
                            inventory_number=inventory_number,
                            defect_description=defect_description,
                            guarantee_type=guarantee_type,
                            status='WAITING',
                            priority=0
                        )
                        equipment_saved = True

                if not equipment_saved:
                    raise ValueError("Не добавлено ни одного оборудования")

                messages.success(request, f'Акт №{act_number} успешно создан!')
                return redirect('roles')

        except Exception as e:
            messages.error(request, f'Ошибка при сохранении акта: {str(e)}')

    # Подготовка контекста для GET запроса
    month_names = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }

    today = timezone.now()
    formatted_date = f"{today.day} {month_names[today.month]} {today.year}"

    context = {
        'page_title': 'Создание акта приёмки',
        'act_number': act_number,
        'formatted_date': formatted_date,
        'clients': clients,
        'categories': categories,
        'brands_by_category': json.dumps(brands_by_category),
        'models_by_brand': json.dumps(models_by_brand),
    }

    return render(request, 'service_center/create_reception_act.html', context)


@login_required
@require_POST
@csrf_exempt
def add_client(request):
    """
    API endpoint для добавления нового клиента через AJAX.
    """
    try:
        data = json.loads(request.body)

        if Client.objects.filter(short_name=data.get('short_name')).exists():
            return JsonResponse({
                'success': False,
                'error': 'Клиент с таким кратким наименованием уже существует'
            })

        client = Client.objects.create(
            short_name=data.get('short_name'),
            full_name=data.get('full_name'),
            contact_person=data.get('contact_person', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', '')
        )

        return JsonResponse({
            'success': True,
            'client': {
                'id': client.id,
                'short_name': client.short_name,
                'full_name': client.full_name,
                'contact_person': client.contact_person,
                'phone': client.phone,
                'email': client.email
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def add_category(request):
    """
    API endpoint для добавления новой категории оборудования через AJAX.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        department = data.get('department', 'NONE')

        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Название категории обязательно'
            })

        if EquipmentCategory.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'error': 'Категория с таким названием уже существует'
            })

        category = EquipmentCategory.objects.create(
            name=name,
            department=department,
            description=data.get('description', '')
        )

        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'department': category.get_department_display()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def add_brand(request):
    """
    API endpoint для добавления нового бренда через AJAX.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        category_id = data.get('category_id')

        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Название бренда обязательно'
            })

        if not category_id:
            return JsonResponse({
                'success': False,
                'error': 'Не выбрана категория'
            })

        try:
            category = EquipmentCategory.objects.get(id=category_id)
        except EquipmentCategory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Категория не найдена'
            })

        # Проверяем уникальность бренда в категории
        if Brand.objects.filter(name=name, category=category).exists():
            return JsonResponse({
                'success': False,
                'error': 'Бренд с таким названием уже существует в этой категории'
            })

        brand = Brand.objects.create(
            name=name,
            category=category,
            description=data.get('description', '')
        )

        return JsonResponse({
            'success': True,
            'brand': {
                'id': brand.id,
                'name': brand.name,
                'category_id': brand.category.id
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def add_model(request):
    """
    API endpoint для добавления новой модели оборудования через AJAX.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        brand_id = data.get('brand_id')
        category_id = data.get('category_id')  # Для проверки

        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Название модели обязательно'
            })

        if not brand_id:
            return JsonResponse({
                'success': False,
                'error': 'Не выбран бренд'
            })

        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Бренд не найден'
            })

        # Проверяем уникальность модели в бренде
        if EquipmentModel.objects.filter(name=name, brand=brand).exists():
            return JsonResponse({
                'success': False,
                'error': 'Модель с таким названием уже существует у этого бренда'
            })

        model = EquipmentModel.objects.create(
            name=name,
            brand=brand,
            category=brand.category,
            description=data.get('description', '')
        )

        return JsonResponse({
            'success': True,
            'model': {
                'id': model.id,
                'name': model.name,
                'brand_id': model.brand.id,
                'category_id': model.category.id
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })