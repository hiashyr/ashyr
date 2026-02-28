# Импорт модулей Django для работы с формами
from django import forms
from django.contrib.auth.forms import UserCreationForm
# Импорт моделей приложения
from .models import CustomUser, Application, Review
# Импорт модуля для работы с регулярными выражениями
import re

# Форма регистрации пользователя
class CustomUserRegistrationForm(forms.ModelForm):
    # Добавление поля пароля
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        help_text='Минимум 8 символов',
        error_messages={
            'required': 'Обязательное поле',
        }
    )

    def __init__(self, *args, **kwargs):
        # Извлекаем флаг из kwargs, по умолчанию True для обратной совместимости
        self.require_password_confirmation = kwargs.pop('require_password_confirmation', True)
        # Извлекаем формат маски телефона, по умолчанию '8'
        self.phone_mask_format = kwargs.pop('phone_mask_format', '8')
        super().__init__(*args, **kwargs)

        # Настройка подсказок для остальных полей
        self.fields['username'].help_text = 'Только латинские буквы и цифры, не менее 6 символов'
        self.fields['fio'].help_text = 'Только кириллические символы и пробелы'
        # Настройка подсказки для телефона в зависимости от формата
        if self.phone_mask_format == '8':
            self.fields['phone'].help_text = 'Формат: 8(XXX)XXX-XX-XX'
        else:
            self.fields['phone'].help_text = 'Формат: +7 (XXX) XXX-XX-XX'
        self.fields['email'].help_text = 'Введите действующий email адрес'

        # Настройка placeholder для телефона в зависимости от формата
        self.fields['phone'].widget.attrs['placeholder'] = '8(XXX)XXX-XX-XX' if self.phone_mask_format == '8' else '+7 (XXX) XXX-XX-XX'

        # Добавляем поле подтверждения пароля если нужно
        if self.require_password_confirmation:
            self.fields['password2'] = forms.CharField(
                label='Подтверждение пароля',
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Повторите пароль'
                }),
                help_text='Повторите пароль для подтверждения',
                error_messages={
                    'required': 'Обязательное поле',
                }
            )

    # Валидация поля username
    def clean_username(self):
        username = self.cleaned_data['username']
        # Проверка формата логина (только латиница и цифры, минимум 6 символов)
        if not re.match(r'^[a-zA-Z0-9]{6,}$', username):
            raise forms.ValidationError('Логин должен содержать только латинские буквы и цифры, минимум 6 символов')

        # Проверка уникальности логина
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует')

        return username

    # Валидация поля fio
    def clean_fio(self):
        fio = self.cleaned_data['fio']
        # Проверка что ФИО содержит только кириллицу и пробелы
        if not re.match(r'^[а-яА-ЯёЁ\s]+$', fio):
            raise forms.ValidationError('ФИО должно содержать только кириллические символы и пробелы')
        return fio

    # Валидация поля phone
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Проверка формата телефона в зависимости от выбранной маски
        if self.phone_mask_format == '8':
            if not re.match(r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$', phone):
                raise forms.ValidationError('Телефон должен быть в формате: 8(XXX)XXX-XX-XX')
        else:
            # Более гибкая валидация для +7: принимаем любые разделители,
            # извлекаем цифры и нормализуем к формату +7 (XXX) XXX-XX-XX
            digits = re.sub(r'\D', '', phone)
            # Если пользователь ввёл 8 в начале, считаем как 7
            if digits.startswith('8'):
                digits = '7' + digits[1:]
            # Ожидаем 11 цифр с ведущей 7
            if not (len(digits) == 11 and digits.startswith('7')):
                raise forms.ValidationError('Телефон должен содержать код страны и 11 цифр, например: +7 (XXX) XXX-XX-XX')
            # Форматируем номер для сохранения в модели
            national = digits[1:]
            formatted = '+7 (' + national[0:3] + ') ' + national[3:6] + '-' + national[6:8] + '-' + national[8:10]
            phone = formatted

        # Проверка уникальности телефона
        if CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Пользователь с таким телефоном уже существует')

        return phone

    # Валидация поля email
    def clean_email(self):
        email = self.cleaned_data['email']

        # Проверка уникальности email
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')

        return email

    # Общая валидация формы
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")

        # Проверяем совпадение паролей только если поле password2 активно
        if self.require_password_confirmation and password1:
            password2 = cleaned_data.get("password2")
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError({
                    'password2': 'Пароли не совпадают'
                })
        elif not self.require_password_confirmation and not password1:
            # Если подтверждение не требуется, но пароль не задан
            raise forms.ValidationError({
                'password1': 'Обязательное поле'
            })

    # Сохранение пользователя с хэшированием пароля
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    class Meta:
        model = CustomUser
        fields = ['username', 'fio', 'phone', 'email', 'password1']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите логин'
            }),
            'fio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ФИО'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'phone-input',
                'inputmode': 'numeric'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email'
            }),
        }
        labels = {
            'username': 'Логин',
            'fio': 'ФИО',
            'phone': 'Телефон',
            'email': 'Email',
            'password1': 'Пароль',
        }
        error_messages = {
            'username': {
                'required': 'Обязательное поле',
            },
            'fio': {
                'required': 'Обязательное поле',
            },
            'phone': {
                'required': 'Обязательное поле',
            },
            'email': {
                'required': 'Обязательное поле',
                'invalid': 'Введите корректный email адрес',
            },
        }

# Форма создания заявки на курс
class ApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавление подсказки для поля даты
        self.fields['desired_start_date'].help_text = 'Формат: ДД.ММ.ГГГГ'
        # Добавляем подсказку для поля курса
        self.fields['course'].help_text = 'Введите название курса'

    class Meta:
        model = Application
        fields = ['course', 'desired_start_date', 'payment_method']
        widgets = {
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название курса'
            }),
            'desired_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'course': 'Наименование курса',
            'desired_start_date': 'Желаемая дата начала обучения',
            'payment_method': 'Способ оплаты',
        }
        error_messages = {
            'course': {
                'required': 'Обязательное поле',
            },
            'desired_start_date': {
                'required': 'Обязательное поле',
            },
            'payment_method': {
                'required': 'Обязательное поле',
            },
        }

# Форма добавления отзыва
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Текст отзыва',
        }
        error_messages = {
            'rating': {
                'required': 'Обязательное поле',
            },
            'text': {
                'required': 'Обязательное поле',
            },
        }


# ===========================================================================
# ПОПУЛЯРНЫЕ ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ В DJANGO
# ===========================================================================

"""
Этот комментарий содержит популярные примеры регулярных выражений для валидации данных в Django.

1. ВАЛИДАЦИЯ EMAIL АДРЕСОВ:
   # Стандартная валидация email
   r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
   
   # Простая валидация email
   r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'

2. ВАЛИДАЦИЯ ТЕЛЕФОННЫХ НОМЕРОВ:
   # Формат +7 (XXX) XXX-XX-XX
   r'^\+7\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$'
   
   # Формат 8(XXX)XXX-XX-XX
   r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$'
   
   # Международный формат
   r'^\+\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{1,9}$'

3. ВАЛИДАЦИЯ ЛОГИНОВ:
   # Только латинские буквы и цифры
   r'^[a-zA-Z0-9]+$'
   
   # Латиница, цифры и подчеркивание
   r'^[a-zA-Z0-9_]+$'
   
   # Только кириллица
   r'^[а-яА-ЯёЁ]+$'
   
   # Кириллица и подчеркивание
   r'^[а-яА-ЯёЁ_]+$'
   
   # Email-подобный логин
   r'^[a-zA-Z0-9@._-]+$'

4. ВАЛИДАЦИЯ ПАРОЛЕЙ:
   # Пароль минимум 8 символов с буквой и цифрой
   r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$'
   
   # Пароль минимум 6 символов
   r'^.{6,}$'
   
   # Пароль с обязательной заглавной буквой
   r'^(?=.*[a-z])(?=.*[A-Z]).{8,}$'

5. ВАЛИДАЦИЯ ФИО:
   # Только кириллица и пробелы
   r'^[а-яА-ЯёЁ\s]+$'
   
   # Кириллица, пробелы и дефис
   r'^[а-яА-ЯёЁ\s-]+$'
   
   # Только латиница и пробелы
   r'^[a-zA-Z\s]+$'

6. ВАЛИДАЦИЯ URL:
   # HTTP и HTTPS URL
   r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
   
   # Простая валидация URL
   r'^https?://\S+$'
   
   # URL с определенными доменами
   r'^https?://(example\.com|test\.com)/.*$'

7. ВАЛИДАЦИЯ ДАТ:
   # Формат ДД.ММ.ГГГГ
   r'^\d{2}\.\d{2}\.\d{4}$'
   
   # Формат ГГГГ-ММ-ДД (ISO)
   r'^\d{4}-\d{2}-\d{2}$'
   
   # Формат ММ/ДД/ГГГГ
   r'^\d{2}/\d{2}/\d{4}$'

8. ВАЛИДАЦИЯ ЧИСЕЛ:
   # Целое число
   r'^-?\d+$'
   
   # Положительное целое число
   r'^\d+$'
   
   # Десятичное число
   r'^-?\d+(\.\d+)?$'
   
   # Число с фиксированной точностью
   r'^-?\d+(\.\d{1,2})?$'

9. ВАЛИДАЦИЯ ИНДЕКСОВ:
   # Российский почтовый индекс
   r'^\d{6}$'
   
   # Американский ZIP-код
   r'^\d{5}(-\d{4})?$'

10. ВАЛИДАЦИЯ ИНН:
    # Российский ИНН (10 цифр)
    r'^\d{10}$'
    
    # Российский ИНН (12 цифр)
    r'^\d{12}$'

11. ВАЛИДАЦИЯ БАНКОВСКИХ КАРТ:
    # Номер карты (16 цифр)
    r'^\d{16}$'
    
    # Номер карты с пробелами
    r'^\d{4}\s\d{4}\s\d{4}\s\d{4}$'

12. ВАЛИДАЦИЯ СЕРИЙНЫХ НОМЕРОВ:
    # Серийный номер (буквы и цифры)
    r'^[A-Z0-9]{8,}$'
    
    # Серийный номер с дефисами
    r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

13. ВАЛИДАЦИЯ ХЕШЕЙ:
    # MD5 хеш
    r'^[a-fA-F0-9]{32}$'
    
    # SHA-1 хеш
    r'^[a-fA-F0-9]{40}$'
    
    # SHA-256 хеш
    r'^[a-fA-F0-9]{64}$'

14. ВАЛИДАЦИЯ ЦВЕТОВ:
    # HEX цвет (#RRGGBB)
    r'^#[0-9A-Fa-f]{6}$'
    
    # HEX цвет короткий (#RGB)
    r'^#[0-9A-Fa-f]{3}$'

15. ВАЛИДАЦИЯ ВРЕМЕНИ:
    # Формат ЧЧ:ММ
    r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    
    # Формат ЧЧ:ММ:СС
    r'^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$'

ПРИМЕР ИСПОЛЬЗОВАНИЯ В DJANGO ФОРМЕ:

from django import forms
from django.core.exceptions import ValidationError
import re

def validate_phone(value):
    if not re.match(r'^\+7\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$', value):
        raise ValidationError('Введите номер в формате: +7 (XXX) XXX-XX-XX')

class MyForm(forms.Form):
    phone = forms.CharField(validators=[validate_phone])

ПРИМЕР ИСПОЛЬЗОВАНИЯ В DJANGO МОДЕЛИ:

from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+7\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$',
    message='Введите номер в формате: +7 (XXX) XXX-XX-XX'
)

class MyModel(models.Model):
    phone = models.CharField(max_length=20, validators=[phone_validator])
"""
