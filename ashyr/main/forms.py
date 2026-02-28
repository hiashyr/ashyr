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