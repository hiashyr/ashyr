# Импорт модулей Django для работы с представлениями
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
# Импорт моделей приложения
from .models import Application, Review
# Импорт форм приложения
from .forms import CustomUserRegistrationForm, ApplicationForm, ReviewForm

# Главная страница сайта
def home(request):
    return render(request, 'home.html')

# Обработка регистрации пользователя
def register(request):
    if request.method == 'POST':
        # Создание формы с данными из POST запроса
        # По умолчанию подтверждение пароля не требуется, формат телефона '8'
        form = CustomUserRegistrationForm( ######################################################
            request.POST,
            require_password_confirmation=False,
            phone_mask_format='8'
        )
        if form.is_valid():
            # Сохранение пользователя и автоматический вход
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('applications')
    else:
        # Создание пустой формы для GET запроса
        # По умолчанию подтверждение паролfя не требуется, формат телефона '8'
        form = CustomUserRegistrationForm( ######################################################
            require_password_confirmation=False,
            phone_mask_format='8'
        )

    return render(request, 'register.html', {'form': form})

# Кастомная страница входа в систему
def custom_login(request):
    if request.method == 'POST':
        # Получение данных из формы
        username = request.POST['username']
        password = request.POST['password']
        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Успешный вход
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.fio}!')
            return redirect('applications')
        else:
            # Ошибка аутентификации
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'login.html')

# Просмотр заявок пользователя (только для авторизованных)
@login_required
def applications(request):
    # Получение всех заявок текущего пользователя
    user_applications = Application.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'applications.html', {'applications': user_applications})

# Создание новой заявки (только для авторизованных)
@login_required
def create_application(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            # Создание заявки без сохранения в БД
            application = form.save(commit=False)
            # Привязка заявки к текущему пользователю
            application.user = request.user
            # Сохранение заявки в БД
            application.save()
            messages.success(request, 'Заявка успешно создана и отправлена на рассмотрение!')
            return redirect('applications')
    else:
        form = ApplicationForm()
    
    return render(request, 'create_application.html', {'form': form})

# Добавление отзыва к заявке (только для авторизованных)
@login_required
def add_review(request, application_id):
    # Получение заявки или 404 ошибка
    application = get_object_or_404(Application, id=application_id, user=request.user)
    
    # Проверка что заявка имеет статус "завершено"
    if application.status != 'completed':
        return HttpResponseForbidden("Отзыв можно оставить только для завершенных курсов")
    
    # Проверка что отзыв еще не оставлен
    if hasattr(application, 'review'):
        messages.error(request, 'Отзыв уже оставлен для этой заявки')
        return redirect('applications')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Создание отзыва без сохранения в БД
            review = form.save(commit=False)
            # Привязка отзыва к заявке
            review.application = application
            # Сохранение отзыва в БД
            review.save()
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('applications')
    else:
        form = ReviewForm()
    
    return render(request, 'add_review.html', {'form': form, 'application': application})

# Выход из системы
def custom_logout(request):
    logout(request)
    return redirect('home')

# Генерация robots.txt для SEO
def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')

# Генерация sitemap.xml для SEO
def sitemap_xml(request):
    return render(request, 'sitemap.xml', content_type='application/xml')