# Импорт модулей Django для работы с моделями
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import re

# Кастомная модель пользователя
class CustomUser(AbstractUser):
    # Валидатор для логина - только латиница и цифры, минимум 6 символов
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9]{6,}$',
        message='Логин должен содержать только латинские буквы и цифры, минимум 6 символов'
    )
    
    # Валидатор для ФИО - только кириллица и пробелы
    fio_validator = RegexValidator(
        regex=r'^[а-яА-ЯёЁ\s]+$',
        message='ФИО должно содержать только кириллические символы и пробелы'
    )
    
    # Валидатор для телефона - строгий формат 8(XXX)XXX-XX-XX
    phone_validator = RegexValidator(
        regex=r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$',
        message='Телефон должен быть в формате: 8(XXX)XXX-XX-XX'
    )

    # Поле логина с валидацией и уникальностью
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Логин',
        error_messages={
            'unique': "Пользователь с таким логином уже существует.",
        },
    )
    # Поле ФИО с валидацией кириллицы
    fio = models.CharField(
        max_length=255,
        validators=[fio_validator],
        verbose_name='ФИО'
    )
    # Поле телефона с валидацией формата
    phone = models.CharField(
        max_length=15,
        validators=[phone_validator],
        verbose_name='Телефон'
    )
    # Поле email с уникальностью
    email = models.EmailField(unique=True, verbose_name='Email')

    # Отключение стандартных полей имени и фамилии
    first_name = None
    last_name = None

    # Поля, обязательные при создании суперпользователя
    REQUIRED_FIELDS = ['email', 'fio', 'phone']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    # Строковое представление пользователя
    def __str__(self):
        return f"{self.fio} ({self.username})"
    
# Модель заявки на обучение
class Application(models.Model):
    # Варианты способов оплаты
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными'),
        ('transfer', 'Переводом по номеру телефона'),
    ]
    
    # Варианты статусов заявки
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'Идет обучение'),
        ('completed', 'Обучение завершено'),
    ]

    # Связь с пользователем (один ко многим)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    # Название курса
    course = models.CharField(max_length=50, verbose_name='Курс')
    # Желаемая дата начала обучения
    desired_start_date = models.DateField(verbose_name='Желаемая дата начала обучения')
    # Способ оплаты с выбором из вариантов
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='Способ оплаты')
    # Статус заявки с выбором из вариантов
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    # Дата создания заявки (автоматически)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    # Дата обновления заявки (автоматически при сохранении)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        # Сортировка по дате создания (новые сверху)
        ordering = ['-created_at']

    # Строковое представление заявки
    def __str__(self):
        return f"Заявка {self.id} - {self.user.fio} - {self.course}"
    

# Модель отзыва к заявке
class Review(models.Model):
    # Связь один-к-одному с заявкой
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        verbose_name='Заявка',
        related_name='review'
    )
    # Текст отзыва
    text = models.TextField(verbose_name='Текст отзыва')
    # Оценка от 1 до 5
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Оценка'
    )
    # Дата создания отзыва (автоматически)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    # Строковое представление отзыва
    def __str__(self):
        return f"Отзыв на заявку {self.application.id}"