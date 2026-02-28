# Импорт административной панели Django
from django.contrib import admin
# Импорт функций для работы с URL
from django.urls import path
# Импорт стандартных views аутентификации
from django.contrib.auth import views as auth_views
# Импорт views из приложения main
from main import views

# Определение URL-шаблонов проекта
urlpatterns = [
    # URL для административной панели Django
    path('admin/', admin.site.urls),
    
    # Главная страница сайта
    path('', views.home, name='home'),
    
    # URL для аутентификации пользователей
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # URL для работы с заявками пользователей
    path('applications/', views.applications, name='applications'),
    path('applications/create/', views.create_application, name='create_application'),
    # URL для добавления отзыва к конкретной заявке
    path('applications/<int:application_id>/review/', views.add_review, name='add_review'),

    # URL для SEO оптимизации
    path('sitemap.xml', views.sitemap_xml, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]