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
from .models import UserRole, Client, EquipmentCategory, Brand, EquipmentModel, ReceptionAct, ReceivedEquipment
import json
from datetime import timedelta
from django.db.models import Count

def login_view(request):
    """
    Представление для входа пользователя.
    """
    if request.user.is_authenticated:
        # Проверяем, есть ли у пользователя роль Приёмщик
        has_receiver_role = UserRole.objects.filter(
            user=request.user,
            role__name='Приёмщик',
            is_active=True
        ).exists()

        if has_receiver_role:
            return redirect('receiver_dashboard')
        else:
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

                # Проверяем, есть ли у пользователя роль Приёмщик
                has_receiver_role = UserRole.objects.filter(
                    user=user,
                    role__name='Приёмщик',
                    is_active=True
                ).exists()

                if has_receiver_role:
                    return redirect('receiver_dashboard')
                else:
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
        return redirect('receiver_dashboard')

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
                print("POST данные:", dict(data))  # Для отладки

                # Обработка клиента
                client_id = data.get('client_id')
                if client_id:
                    client = Client.objects.get(id=client_id)
                    # Обновляем поля клиента
                    client.contact_person = data.get('contact_person', '')
                    client.phone = data.get('phone', '')
                    client.email = data.get('email', '')
                    client.save()
                    print(f"Клиент обновлен: {client.short_name}")  # Для отладки
                else:
                    raise ValueError("Клиент не выбран")

                # Создаем акт приёмки
                act = ReceptionAct.objects.create(
                    act_number=act_number,
                    client=client,
                    receiver=request.user
                )
                print(f"Акт создан: {act.act_number}")  # Для отладки

                # Обработка оборудования
                equipment_count = int(data.get('equipment_count', 0))
                equipment_saved = False
                print(f"Количество оборудования: {equipment_count}")  # Для отладки

                for i in range(equipment_count):
                    category_id = data.get(f'equipment_{i}_category')
                    brand_id = data.get(f'equipment_{i}_brand')
                    model_id = data.get(f'equipment_{i}_model')
                    serial_number = data.get(f'equipment_{i}_serial_number', 'Без номера')
                    inventory_number = data.get(f'equipment_{i}_inventory_number', '')
                    guarantee_type = data.get(f'equipment_{i}_guarantee_type', 'NONE')
                    defect_description = data.get(f'equipment_{i}_defect_description', '')

                    print(
                        f"Оборудование {i}: category={category_id}, brand={brand_id}, model={model_id}")  # Для отладки

                    # Проверяем, что модель выбрана
                    if model_id and model_id != '' and model_id != 'new_model':
                        try:
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
                            print(f"Оборудование {i} сохранено: {equipment_model.name}")  # Для отладки
                        except EquipmentModel.DoesNotExist:
                            print(f"Ошибка: модель с ID {model_id} не найдена")
                        except Exception as e:
                            print(f"Ошибка при сохранении оборудования {i}: {str(e)}")

                if not equipment_saved:
                    raise ValueError("Не добавлено ни одного оборудования")

                messages.success(request, f'Акт №{act_number} успешно создан!')
                return redirect('receiver_dashboard')

        except Exception as e:
            print(f"Ошибка при сохранении акта: {str(e)}")  # Для отладки
            messages.error(request, f'Ошибка при сохранении акта: {str(e)}')
            # Возвращаем на ту же страницу с сохраненными данными

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


@login_required
def receiver_dashboard_view(request):
    """
    Панель управления для приёмщика.
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

    # Получаем оборудование готовое к выдаче (статус READY)
    ready_equipment = ReceivedEquipment.objects.filter(
        status='READY'
    ).select_related(
        'reception_act__client',
        'model__brand',
        'model__category'
    ).order_by('-created_at')

    # Получаем акты приёмки за последние 3 дня
    three_days_ago = timezone.now() - timedelta(days=3)
    recent_acts = ReceptionAct.objects.filter(
        created_at__gte=three_days_ago
    ).annotate(
        equipment_count=Count('equipments')
    ).select_related('client').order_by('-created_at')

    context = {
        'page_title': 'Панель приёмщика',
        'ready_equipment': ready_equipment,
        'recent_acts': recent_acts,
    }

    return render(request, 'service_center/receiver_dashboard.html', context)


@login_required
def reception_act_detail(request, act_id):
    """
    Детальный просмотр акта приёмки.
    """
    # Проверяем, есть ли у пользователя роль Приёмщик
    has_receiver_role = UserRole.objects.filter(
        user=request.user,
        role__name='Приёмщик',
        is_active=True
    ).exists()

    if not has_receiver_role:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('receiver_dashboard')

    # Получаем акт приёмки со связанными данными
    act = get_object_or_404(
        ReceptionAct.objects.select_related('client', 'receiver'),
        id=act_id
    )

    # Получаем оборудование из этого акта
    equipment_list = ReceivedEquipment.objects.filter(reception_act=act).select_related('model__brand', 'model__category')

    context = {
        'page_title': f'Акт приёмки №{act.act_number}',
        'act': act,
        'equipment_list': equipment_list,
    }

    return render(request, 'service_center/reception_act_detail.html', context)


@login_required
def coordinator_dashboard_view(request):
    """
    Панель управления для координатора.
    """
    # Проверяем, есть ли у пользователя роль Координатор
    has_coordinator_role = UserRole.objects.filter(
        user=request.user,
        role__name='Координатор',
        is_active=True
    ).exists()

    if not has_coordinator_role:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('roles')

    # Получаем оборудование со всеми статусами кроме 'ISSUED' (выдано)
    equipment_list = ReceivedEquipment.objects.exclude(
        status='ISSUED'
    ).select_related(
        'reception_act__client',
        'model__brand',
        'model__category'
    ).order_by('created_at')  # старые сверху

    # Вычисляем количество дней в ремонте для каждого оборудования
    today = timezone.now().date()
    for equipment in equipment_list:
        # Вычисляем разницу в днях между сегодняшней датой и датой создания записи
        equipment.days_in_repair = (today - equipment.created_at.date()).days

    context = {
        'page_title': 'Панель координатора',
        'equipment_list': equipment_list,
    }

    return render(request, 'service_center/coordinator_dashboard.html', context)


@login_required
@require_POST
@csrf_exempt
def update_equipment_priority(request):
    """
    API endpoint для обновления приоритета оборудования.
    """
    try:
        data = json.loads(request.body)
        equipment_id = data.get('equipment_id')
        priority = data.get('priority')

        if not equipment_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указано оборудование'
            })

        if priority not in [0, 1, 3]:  # Разрешённые значения приоритета
            return JsonResponse({
                'success': False,
                'error': 'Недопустимое значение приоритета'
            })

        # Проверяем, есть ли у пользователя роль Координатор
        has_coordinator_role = UserRole.objects.filter(
            user=request.user,
            role__name='Координатор',
            is_active=True
        ).exists()

        if not has_coordinator_role:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав для выполнения этой операции'
            })

        equipment = ReceivedEquipment.objects.get(id=equipment_id)
        equipment.priority = priority
        equipment.save()

        return JsonResponse({
            'success': True,
            'message': 'Приоритет обновлён'
        })

    except ReceivedEquipment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Оборудование не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def update_equipment_status(request):
    """
    API endpoint для обновления статуса оборудования.
    """
    try:
        data = json.loads(request.body)
        equipment_id = data.get('equipment_id')
        status = data.get('status')

        if not equipment_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указано оборудование'
            })

        # Проверяем, есть ли у пользователя роль Координатор
        has_coordinator_role = UserRole.objects.filter(
            user=request.user,
            role__name='Координатор',
            is_active=True
        ).exists()

        if not has_coordinator_role:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав для выполнения этой операции'
            })

        equipment = ReceivedEquipment.objects.get(id=equipment_id)

        # Проверяем, что статус допустимый
        valid_statuses = dict(ReceivedEquipment.STATUS_CHOICES).keys()
        if status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Недопустимый статус'
            })

        equipment.status = status
        equipment.save()

        return JsonResponse({
            'success': True,
            'message': 'Статус обновлён'
        })

    except ReceivedEquipment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Оборудование не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def update_equipment_guarantee(request):
    """
    API endpoint для обновления типа гарантии оборудования.
    """
    try:
        data = json.loads(request.body)
        equipment_id = data.get('equipment_id')
        guarantee_type = data.get('guarantee_type')

        if not equipment_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указано оборудование'
            })

        # Проверяем, есть ли у пользователя роль Координатор
        has_coordinator_role = UserRole.objects.filter(
            user=request.user,
            role__name='Координатор',
            is_active=True
        ).exists()

        if not has_coordinator_role:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав для выполнения этой операции'
            })

        equipment = ReceivedEquipment.objects.get(id=equipment_id)

        # Проверяем, что тип гарантии допустимый
        valid_guarantee_types = dict(ReceivedEquipment.GUARANTEE_CHOICES).keys()
        if guarantee_type not in valid_guarantee_types:
            return JsonResponse({
                'success': False,
                'error': 'Недопустимый тип гарантии'
            })

        equipment.guarantee_type = guarantee_type
        equipment.save()

        return JsonResponse({
            'success': True,
            'message': 'Тип гарантии обновлён'
        })

    except ReceivedEquipment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Оборудование не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })