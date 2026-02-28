# Импорт модулей Django для работы с моделями
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
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
    
    # Гибкий валидатор для телефона: проверяет наличие 11 цифр и ведущей 7/8
    def phone_flex_validator(value):
        digits = re.sub(r'\D', '', value or '')
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        if not (len(digits) == 11 and digits.startswith('7')):
            raise ValidationError('Телефон должен содержать код страны и 11 цифр, например: +7 (XXX) XXX-XX-XX')

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
    # Поле телефона с гибкой валидацией; значение будет нормализовано при сохранении
    phone = models.CharField(
        max_length=32,
        validators=[phone_flex_validator],
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

    # Нормализация телефона перед сохранением: сохраняем в формате +7 (XXX) XXX-XX-XX
    def save(self, *args, **kwargs):
        if self.phone:
            digits = re.sub(r'\D', '', self.phone)
            if digits.startswith('8'):
                digits = '7' + digits[1:]
            if len(digits) >= 11 and digits.startswith('7'):
                national = digits[1:11]
                self.phone = '+7 (' + national[0:3] + ') ' + national[3:6] + '-' + national[6:8] + '-' + national[8:10]
        super().save(*args, **kwargs)
    
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