"""
Админ-панель Django для приложения ServiceHub.

Этот файл регистрирует все модели из models.py в админ-панели Django,
настраивает отображение, фильтрацию, поиск и действия для удобного управления данными.

Каждая модель имеет свой класс ModelAdmin с настройками, оптимизированными для работы с данными сервисного центра.
"""

from django.contrib import admin
from .models import (
    Role, UserRole, Client, EquipmentCategory,
    Brand, EquipmentModel, ReceptionAct, ReceivedEquipment
)

# 1. РЕГИСТРАЦИЯ СТАНДАРТНОЙ МОДЕЛИ USER С ДОПОЛНИТЕЛЬНЫМИ ПОЛЯМИ
# -----------------------------------------------------------------
class UserRoleInline(admin.TabularInline):
    """
    Встроенное отображение ролей пользователя на странице редактирования User.

    Позволяет управлять ролями пользователя прямо на его странице в админке.
    """
    model = UserRole
    extra = 0  # Не показывать пустые формы для новых ролей по умолчанию
    verbose_name = "Роль пользователя"
    verbose_name_plural = "Роли пользователя"


# 2. АДМИНКА ДЛЯ МОДЕЛИ ROLE
# -----------------------------------------------------------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Админка для управления ролями в системе.

    Роли определяют уровень доступа и функциональность пользователей.
    """
    list_display = ('name', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Сворачиваемый блок
        }),
    )


# 3. АДМИНКА ДЛЯ МОДЕЛИ USERROLE
# -----------------------------------------------------------------
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """
    Админка для связи пользователей с ролями.

    Управление назначением ролей пользователям и их активностью.
    """
    list_display = ('user', 'role', 'assigned_at', 'is_active')
    list_filter = ('is_active', 'role', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'role__name')
    readonly_fields = ('assigned_at',)
    list_editable = ('is_active',)  # Позволяет менять активность прямо из списка
    ordering = ('-assigned_at',)  # Новые назначения сверху


# 4. АДМИНКА ДЛЯ МОДЕЛИ CLIENT
# -----------------------------------------------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Админка для управления клиентами сервисного центра.

    Клиенты - организации или физические лица, сдающие оборудование в ремонт.
    """
    list_display = ('short_name', 'full_name', 'contact_person', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('short_name', 'full_name', 'contact_person', 'phone', 'email')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('short_name', 'full_name', 'contact_person')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# 5. АДМИНКА ДЛЯ МОДЕЛИ EQUIPMENTCATEGORY
# -----------------------------------------------------------------
@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    """
    Админка для управления категориями оборудования.

    Категории группируют оборудование по типам (сварочное, электроинструмент и т.д.).
    """
    list_display = ('name', 'department', 'get_brands_count', 'get_models_count')
    list_filter = ('department',)
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'department')
        }),
    )

    def get_brands_count(self, obj):
        """
        Отображает количество брендов в категории.

        Args:
            obj: Объект категории

        Returns:
            int: Количество брендов
        """
        return obj.brands.count()

    get_brands_count.short_description = "Кол-во брендов"

    def get_models_count(self, obj):
        """
        Отображает количество моделей в категории.

        Args:
            obj: Объект категории

        Returns:
            int: Количество моделей
        """
        return obj.models.count()

    get_models_count.short_description = "Кол-во моделей"


# 6. АДМИНКА ДЛЯ МОДЕЛИ BRAND
# -----------------------------------------------------------------
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """
    Админка для управления брендами оборудования.

    Бренды (производители) оборудования, привязанные к категориям.
    """
    list_display = ('name', 'category', 'get_models_count')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)  # Автодополнение для категории
    list_select_related = ('category',)  # Оптимизация запросов к БД
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description')
        }),
    )

    def get_models_count(self, obj):
        """
        Отображает количество моделей у бренда.

        Args:
            obj: Объект бренда

        Returns:
            int: Количество моделей
        """
        return obj.models.count()

    get_models_count.short_description = "Кол-во моделей"


# 7. АДМИНКА ДЛЯ МОДЕЛИ EQUIPMENTMODEL
# -----------------------------------------------------------------
@admin.register(EquipmentModel)
class EquipmentModelAdmin(admin.ModelAdmin):
    """
    Админка для управления конкретными моделями оборудования.

    Модели оборудования, принадлежащие определённым брендам и категориям.
    """
    list_display = ('name', 'brand', 'category', 'get_equipment_count')
    list_filter = ('category', 'brand')
    search_fields = ('name', 'description', 'brand__name')
    autocomplete_fields = ('category', 'brand')  # Автодополнение для связанных полей
    list_select_related = ('category', 'brand')  # Оптимизация запросов
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'brand', 'description')
        }),
    )

    def get_equipment_count(self, obj):
        """
        Отображает количество принятого оборудования этой модели.

        Args:
            obj: Объект модели оборудования

        Returns:
            int: Количество оборудования
        """
        return obj.receivedequipment_set.count()

    get_equipment_count.short_description = "Принято единиц"


# 8. АДМИНКА ДЛЯ МОДЕЛИ RECEPTIONACT
# -----------------------------------------------------------------
class ReceivedEquipmentInline(admin.TabularInline):
    """
    Встроенное отображение принятого оборудования на странице акта приёмки.

    Позволяет видеть и редактировать всё оборудование по акту на одной странице.
    """
    model = ReceivedEquipment
    extra = 0  # Не показывать пустые формы по умолчанию
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'model', 'serial_number', 'inventory_number',
        'defect_description', 'status', 'priority'
    )
    autocomplete_fields = ('model', 'assigned_specialist')
    verbose_name = "Принятое оборудование"
    verbose_name_plural = "Принятое оборудование"


@admin.register(ReceptionAct)
class ReceptionActAdmin(admin.ModelAdmin):
    """
    Админка для управления актами приёмки оборудования.

    Акты документируют передачу оборудования от клиента в сервисный центр.
    """
    list_display = ('act_number', 'client', 'receiver', 'created_at', 'get_equipment_count', 'guarantee_type')
    list_filter = ('created_at', 'guarantee_type', 'client', 'receiver')
    search_fields = ('act_number', 'client__short_name', 'client__full_name')
    readonly_fields = ('act_number', 'created_at', 'updated_at', 'printed_at')
    autocomplete_fields = ('client', 'receiver')  # Автодополнение для клиента и приёмщика
    inlines = [ReceivedEquipmentInline]  # Встроенное отображение оборудования
    list_select_related = ('client', 'receiver')  # Оптимизация запросов
    actions = ['mark_as_printed']
    fieldsets = (
        ('Основная информация', {
            'fields': ('act_number', 'client', 'receiver', 'guarantee_type')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'printed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_equipment_count(self, obj):
        """
        Отображает количество оборудования в акте.

        Args:
            obj: Объект акта приёмки

        Returns:
            int: Количество оборудования
        """
        return obj.equipments.count()

    get_equipment_count.short_description = "Кол-во оборудования"

    def mark_as_printed(self, request, queryset):
        """
        Действие для отметки актов как распечатанных.

        Устанавливает текущую дату и время в поле printed_at.

        Args:
            request: Объект запроса
            queryset: Выбранные объекты актов
        """
        from django.utils import timezone
        updated = queryset.update(printed_at=timezone.now())
        self.message_user(request, f"{updated} актов отмечены как распечатанные.")

    mark_as_printed.short_description = "Отметить как распечатанные"


# 9. АДМИНКА ДЛЯ МОДЕЛИ RECEIVEDEQUIPMENT
# -----------------------------------------------------------------
@admin.register(ReceivedEquipment)
class ReceivedEquipmentAdmin(admin.ModelAdmin):
    """
    Админка для управления принятым оборудованием.

    Отдельные единицы оборудования, принятые по актам приёмки.
    """
    list_display = (
        'get_full_name', 'reception_act', 'serial_number',
        'status', 'priority', 'assigned_specialist', 'created_at'
    )
    list_filter = ('status', 'guarantee_type', 'priority', 'created_at', 'assigned_specialist')
    search_fields = (
        'serial_number', 'inventory_number',
        'model__name', 'model__brand__name',
        'reception_act__act_number'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('reception_act', 'model', 'assigned_specialist')
    list_select_related = ('reception_act', 'model', 'model__brand', 'model__category', 'assigned_specialist')
    list_editable = ('status', 'priority')  # Позволяет менять статус и приоритет прямо из списка
    actions = ['assign_default_specialist', 'set_high_priority']
    fieldsets = (
        ('Основная информация', {
            'fields': ('reception_act', 'model', 'serial_number', 'inventory_number')
        }),
        ('Описание проблемы', {
            'fields': ('defect_description', 'audio_description')
        }),
        ('Ремонт', {
            'fields': ('guarantee_type', 'assigned_specialist', 'status', 'priority')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        """
        Отображает полное название оборудования.

        Args:
            obj: Объект принятого оборудования

        Returns:
            str: Полное название оборудования
        """
        return obj.get_full_name()

    get_full_name.short_description = "Оборудование"

    def assign_default_specialist(self, request, queryset):
        """
        Действие для автоматического назначения специалиста по умолчанию.

        Назначает специалиста, ответственного за категорию оборудования.
        Поскольку поле assigned_specialist удалено из EquipmentCategory,
        эта функция больше не может автоматически назначать специалиста.
        Оставлена для совместимости, но всегда возвращает сообщение об отсутствии специалиста.

        Args:
            request: Объект запроса
            queryset: Выбранные объекты оборудования
        """
        updated = 0
        for equipment in queryset:
            default_specialist = equipment.get_default_specialist()
            if default_specialist and equipment.assigned_specialist != default_specialist:
                equipment.assigned_specialist = default_specialist
                equipment.save()
                updated += 1

        if updated > 0:
            self.message_user(request, f"Специалист назначен для {updated} единиц оборудования.")
        else:
            self.message_user(request, "Не удалось назначить специалиста по умолчанию. Специалист по категории не установлен.")

    assign_default_specialist.short_description = "Назначить специалиста по умолчанию"

    def set_high_priority(self, request, queryset):
        """
        Действие для установки высокого приоритета (80) для выбранного оборудования.

        Args:
            request: Объект запроса
            queryset: Выбранные объекты оборудования
        """
        updated = queryset.update(priority=80)
        self.message_user(request, f"Высокий приоритет установлен для {updated} единиц оборудования.")

    set_high_priority.short_description = "Установить высокий приоритет"

    def get_queryset(self, request):
        """
        Оптимизация запросов к базе данных.

        Предзагружает все связанные объекты для уменьшения количества SQL-запросов.

        Args:
            request: Объект запроса

        Returns:
            QuerySet: Оптимизированный QuerySet
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'reception_act',
            'model',
            'model__brand',
            'model__category',
            'assigned_specialist',
            'assigned_specialist__user',
            'assigned_specialist__role'
        )


# 10. НАСТРОЙКИ АДМИН-ПАНЕЛИ
# -----------------------------------------------------------------
admin.site.site_header = "ServiceHub - Администрирование"
admin.site.site_title = "ServiceHub Admin"
admin.site.index_title = "Управление сервисным центром"

# Группировка моделей в админке для удобства навигации
# (Django автоматически группирует модели по приложениям, но можно настроить иначе)