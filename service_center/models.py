"""
Модели базы данных для сервисного центра ServiceHub.

Этот файл определяет все модели данных приложения, включая:
- Роли пользователей и их назначение
- Клиентов
- Категории, бренды и модели оборудования
- Акты приёмки и принятое оборудование

Все модели используют Django ORM для взаимодействия с базой данных SQLite.
"""

from django.db import models
from django.contrib.auth.models import User  # Стандартная модель пользователя Django


class Role(models.Model):
    """
    Модель для хранения ролей в системе.

    Роли определяют уровень доступа и функциональность пользователей.
    Примеры ролей: Приёмщик, Координатор, Специалист и т.д.

    Attributes:
        name (CharField): Название роли (например, "Специалист")
        description (TextField): Подробное описание роли и её функций
        created_at (DateTimeField): Дата и время создания записи (автоматически)
        updated_at (DateTimeField): Дата и время последнего обновления (автоматически)
    """

    # Название роли, обязательно для заполнения, максимальная длина 100 символов
    name = models.CharField(max_length=100, verbose_name="Название роли")

    # Подробное описание роли, необязательное поле
    description = models.TextField(blank=True, null=True, verbose_name="Описание роли")

    # Автоматически устанавливается при создании записи
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Автоматически обновляется при каждом сохранении записи
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Название роли
        """
        return self.name

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['name']  # Сортировка по умолчанию по названию роли
        verbose_name = "Роль"  # Название в единственном числе для админки
        verbose_name_plural = "Роли"  # Название во множественном числе для админки


class UserRole(models.Model):
    """
    Модель для связи пользователей с ролями (многие-ко-многим через промежуточную модель).

    Позволяет назначать пользователям несколько ролей и управлять их активностью.

    Attributes:
        user (ForeignKey): Ссылка на пользователя Django
        role (ForeignKey): Ссылка на роль
        assigned_at (DateTimeField): Дата и время назначения роли (автоматически)
        is_active (BooleanField): Флаг активности роли у пользователя
    """

    # Связь с моделью User Django (один пользователь может иметь несколько UserRole)
    # on_delete=models.CASCADE: при удалении пользователя удаляются все его UserRole
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    # Связь с моделью Role (одна роль может быть у нескольких пользователей)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")

    # Дата и время назначения роли пользователю (устанавливается автоматически при создании)
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")

    # Флаг активности роли. Если False, роль считается недействительной для пользователя
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        # Уникальная комбинация пользователя и роли (чтобы нельзя было назначить одну роль дважды)
        unique_together = ('user', 'role')
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Имя пользователя и название его роли
        """
        return f"{self.user.username} - {self.role.name}"


class Client(models.Model):
    """
    Модель для хранения информации о клиентах сервисного центра.

    Клиенты - это организации или физические лица, сдающие оборудование в ремонт.

    Attributes:
        short_name (CharField): Краткое наименование (обязательное, уникальное)
        full_name (CharField): Полное наименование (обязательное, уникальное)
        contact_person (CharField): ФИО ответственного лица
        phone (CharField): Контактный телефон
        email (EmailField): Электронная почта (необязательное)
        address (TextField): Адрес клиента (необязательное)
        created_at (DateTimeField): Дата создания записи (автоматически)
    """

    # Краткое наименование клиента (например, "Ромашка")
    # unique=True: гарантирует уникальность значения в базе данных
    short_name = models.CharField(max_length=50, unique=True, verbose_name="Краткое наименование клиента")

    # Полное официальное наименование (например, "ООО Ромашка")
    full_name = models.CharField(max_length=100, unique=True, verbose_name="Полное наименование клиента")

    # ФИО лица, ответственного за взаимодействие с сервисным центром
    contact_person = models.CharField(max_length=200, verbose_name="Ответственное лицо")

    # Контактный телефон для связи
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    # Электронная почта, необязательное поле
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    # Юридический или фактический адрес клиента, необязательное поле
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    # Дата и время создания записи о клиенте
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Краткое наименование клиента
        """
        return self.short_name

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['short_name']  # Сортировка по краткому наименованию
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class EquipmentCategory(models.Model):
    """
    Модель для категорий оборудования.

    Категории группируют оборудование по типам (например, сварочное, электроинструмент и т.д.).

    Attributes:
        name (CharField): Название категории (обязательное, уникальное)
        description (TextField): Описание категории (необязательное)
    """
    DEPARTAMENT_CHOICES = [
        ('NONE', 'Не определён'),
        ('MOTOR', 'Цех агрегатов'),
        ('ELECTRO', 'Цех электроинструмента'),
        ('SMALL', 'Цех малой маханизации'),
        ('ELECTRON', 'Цех электроники')
    ]

    # Название категории оборудования (например, "Сварочные аппараты")
    name = models.CharField(max_length=200, unique=True, verbose_name="Название категории")

    # Подробное описание категории, её особенностей
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    department = models.CharField(max_length=10, choices=DEPARTAMENT_CHOICES, default='NONE',
                                  verbose_name="Цех обслуживания")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Название категории оборудования
        """
        return self.name

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['name']  # Сортировка по названию категории
        verbose_name = "Категория оборудования"
        verbose_name_plural = "Категории оборудования"


class Brand(models.Model):
    """
    Модель для брендов (производителей) оборудования.

    Каждый бренд принадлежит определённой категории оборудования.

    Attributes:
        name (CharField): Название бренда (обязательное, уникальное в пределах категории)
        category (ForeignKey): Категория оборудования
        description (TextField): Дополнительная информация о бренде (необязательное)
    """

    # Название бренда/производителя (например, "Bosch", "Resanta")
    name = models.CharField(max_length=20, unique=False, verbose_name="Название бренда")

    # Категория оборудования, к которой относится бренд
    # on_delete=models.CASCADE: при удалении категории удаляются все её бренды
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE,
                                 related_name='brands', verbose_name="Категория")

    # Дополнительная информация о бренде (история, особенности и т.д.)
    description = models.TextField(blank=True, null=True, verbose_name="Дополнительные заметки")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Название бренда
        """
        return self.name

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['name']  # Сортировка по названию бренда
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        # Уникальная комбинация названия бренда и категории
        unique_together = ('name', 'category')


class EquipmentModel(models.Model):
    """
    Модель для конкретных моделей оборудования.

    Каждая модель принадлежит определённому бренду и категории.

    Attributes:
        category (ForeignKey): Категория оборудования
        brand (ForeignKey): Бренд производителя
        name (CharField): Название модели
        description (TextField): Дополнительная информация о модели (необязательное)
    """

    # Категория оборудования (дублируется для удобства запросов)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE,
                                 related_name='models', verbose_name="Категория оборудования")

    # Бренд производителя
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='models', verbose_name="Бренд")

    # Название конкретной модели (например, "САИ-250А")
    name = models.CharField(max_length=200, verbose_name="Название модели")

    # Технические характеристики, особенности модели
    description = models.TextField(blank=True, null=True, verbose_name="Дополнительные заметки")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Название бренда и модели
        """
        return f"{self.brand.name} {self.name}"

    def get_full_name(self):
        """
        Полное название оборудования в формате "Категория Бренд Модель".

        Returns:
            str: Полное название оборудования
        """
        return f"{self.category.name} {self.brand.name} {self.name}"

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['name']  # Сортировка по названию модели
        verbose_name = "Модель оборудования"
        verbose_name_plural = "Модели оборудования"
        # Уникальная комбинация названия модели и бренда
        unique_together = ('name', 'brand')


class ReceptionAct(models.Model):
    """
    Модель для актов приёмки оборудования.

    Акты приёмки документируют передачу оборудования от клиента в сервисный центр.
    Один акт может содержать несколько единиц оборудования.

    Attributes:

        act_number (CharField): Уникальный номер акта
        created_at (DateTimeField): Дата и время создания акта (автоматически)
        client (ForeignKey): Клиент, сдавший оборудование
        receiver (ForeignKey): Приёмщик, оформивший акт

        updated_at (DateTimeField): Дата и время обновления акта (автоматически)
        printed_at (DateTimeField): Дата и время печати акта (необязательное)
    """

    # Уникальный номер акта, генерируется автоматически
    act_number = models.CharField(max_length=50, unique=True, verbose_name="Номер акта")

    # Дата и время создания акта
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Клиент, сдавший оборудование
    # on_delete=models.PROTECT: предотвращает удаление клиента, если есть акты
    client = models.ForeignKey(Client, on_delete=models.PROTECT,
                               related_name='reception_acts', verbose_name="Клиент")

    # Пользователь, принявший оборудование (приёмщик)
    receiver = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name='reception_acts', verbose_name="Приёмщик")

    # Дата и время последнего обновления акта
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # Дата и время фактической печати акта (если был распечатан)
    printed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата печати")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.

        Returns:
            str: Номер акта, дата и клиент
        """
        return f"Акт №{self.act_number} от {self.created_at.strftime('%d.%m.%Y')} - {self.client.short_name}"

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        ordering = ['-created_at']  # Сортировка по дате создания (новые сверху)
        verbose_name = "Акт приёмки"
        verbose_name_plural = "Акты приёмки"

    @staticmethod
    def generate_act_number():
        """
        Генерация уникального номера акта в формате ACT-YYYYMMDD-XXXX.

        Формат: ACT-20240105-1234
        - ACT: префикс
        - 20240105: дата в формате ГГГГММДД
        - 1234: случайное 4-значное число

        Returns:
            str: Сгенерированный номер акта
        """
        from django.utils import timezone
        import random

        # Текущая дата в формате ГГГГММДД
        date_str = timezone.now().strftime('%Y%m%d')

        # Случайное 4-значное число с лидирующими нулями
        random_str = f"{random.randint(1000, 9999):04d}"

        return f"ACT-{date_str}-{random_str}"


class ReceivedEquipment(models.Model):
    """
    Модель для принятого оборудования.

    Каждая запись представляет собой одну единицу оборудования, принятую по акту.

    Attributes:
        GUARANTEE_CHOICES: Варианты типов гарантии для оборудования
        STATUS_CHOICES: Варианты статусов оборудования в процессе ремонта
        reception_act (ForeignKey): Акт приёмки
        model (ForeignKey): Модель оборудования
        serial_number (CharField): Серийный номер (необязательное)
        inventory_number (CharField): Инвентарный номер клиента (необязательное)
        defect_description (TextField): Описание неисправности со слов клиента
        guarantee_type (CharField): Тип гарантии для этого оборудования
        assigned_specialist (ForeignKey): Назначенный специалист для ремонта
        status (CharField): Текущий статус оборудования в процессе ремонта
        priority (IntegerField): Приоритет ремонта (0-100)
        created_at (DateTimeField): Дата и время создания записи (автоматически)
        updated_at (DateTimeField): Дата и время обновления записи (автоматически)
    """

    # Варианты типов гарантии для конкретного оборудования
    GUARANTEE_CHOICES = [
        ('NONE', 'Без гарантии'),
        ('FACTORY', 'Заводская гарантия'),
        ('SERVICE', 'Гарантия сервисного центра'),
    ]

    # Статусы оборудования в процессе ремонта
    STATUS_CHOICES = [
        ('WAITING', 'Ожидает распределения'),
        ('ASSIGNED', 'Назначено специалисту'),
        ('DIAGNOSIS', 'На диагностике'),
        ('DIAGNOSED', 'Диагностировано'),
        ('APPROVAL', 'Согласование стоимости'),
        ('PARTS', 'Ожидает запчастей'),
        ('REPAIR', 'В ремонте'),
        ('TESTING', 'На испытаниях'),
        ('READY', 'Готово к выдаче'),
        ('ISSUED', 'Выдано'),
    ]

    # Акт приёмки, к которому относится оборудование
    # on_delete=models.CASCADE: при удалении акта удаляется всё его оборудование
    reception_act = models.ForeignKey(ReceptionAct, on_delete=models.CASCADE,
                                      related_name='equipments', verbose_name="Акт приёмки")

    # Конкретная модель оборудования
    # on_delete=models.PROTECT: предотвращает удаление модели, если есть оборудование
    model = models.ForeignKey(EquipmentModel, on_delete=models.PROTECT,
                              verbose_name="Модель оборудования")

    # Серийный номер, присвоенный заводом-изготовителем
    # default="Без номера": значение по умолчанию если номер не указан
    serial_number = models.CharField(max_length=30, default="---",
                                     blank=True, verbose_name="Серийный номер")

    # Инвентарный номер, присвоенный клиентом для внутреннего учёта
    inventory_number = models.CharField(max_length=30, default="---", blank=True, null=True,
                                        verbose_name="Инвентарный номер")

    # Описание проблемы/неисправности со слов клиента
    defect_description = models.CharField(max_length=300, blank=True, null=True,
                                          verbose_name="Описание неисправности")

    # Тип гарантии для этого конкретного оборудования
    guarantee_type = models.CharField(max_length=10, choices=GUARANTEE_CHOICES,
                                      default='NONE', verbose_name="Тип гарантии")

    # Специалист, назначенный для ремонта этого оборудования
    assigned_specialist = models.ForeignKey(
        UserRole,
        on_delete=models.SET_NULL,  # При удалении специалиста поле становится NULL
        null=True,
        blank=True,
        verbose_name="Назначенный специалист",
        related_name='assigned_equipment'  # Имя для обратной связи
    )

    # Текущий статус оборудования в процессе ремонта
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='WAITING', verbose_name="Статус")

    # Приоритет ремонта (0 - низкий, 100 - высокий)
    # Используется для определения порядка выполнения работ
    priority = models.IntegerField(default=0, verbose_name="Приоритет")

    # Дата и время создания записи об оборудовании
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Дата и время последнего обновления записи
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        """
        Строковое представление объекта для отображения в админке и в логах.
        Returns:  str: Модель оборудования и серийный номер
        """
        return f"{self.model} (Серийный: {self.serial_number})"

    def get_full_name(self):
        """
        Полное название оборудования в формате "Категория Бренд Модель".

        Returns:
            str: Полное название оборудования
        """
        return f"{self.model.category.name} {self.model.brand.name} {self.model.name}"

    def get_status_color(self):
        """
        Определяет цвет статуса для отображения в интерфейсе (Bootstrap).
        Каждый статус имеет свой цвет для визуального различия.
        Returns:  str: Название класса цвета Bootstrap
        """
        colors = {
            'WAITING': 'primary',  # Серый primary
            'ASSIGNED': 'info',  # Синий
            'DIAGNOSIS': 'warning',  # Жёлтый
            'DIAGNOSED': 'secondary',  # Темно-синий secondary
            'APPROVAL': 'warning',  # Жёлтый
            'PARTS': 'danger',  # Красный
            'REPAIR': 'info',  # Синий
            'TESTING': 'success',  # Зелёный
            'READY': 'success',  # Зелёный
            'ISSUED': 'dark',  # Тёмный
        }
        return colors.get(self.status, 'secondary')

    def get_guarantee_color(self):
        """
        Определяет цвет гарантии для отображения в интерфейсе (Bootstrap).
        Каждая гарантия имеет свой цвет для визуального различия.
        Returns:  str: Название класса цвета Bootstrap
        """
        colors = {
            'NONE': 'primary',  # Серый
            'SERVICE': 'warning',  # Жёлтый
            'FACTORY': 'danger',  # Красный
            }
        return colors.get(self.guarantee_type, 'secondary')

    class Meta:
        """
        Метаданные модели для настройки отображения в админке и поведения.
        """
        # Сортировка по приоритету (высокий сверху) и дате создания (новые сверху)
        ordering = ['-priority', '-created_at']
        verbose_name = "Принятое оборудование"
        verbose_name_plural = "Принятое оборудование"