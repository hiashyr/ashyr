# Импорт стандартных административных модулей Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
# Импорт модели Theme из admin-interface
from admin_interface.models import Theme
# Импорт моделей приложения
from .models import CustomUser, Application, Review

# Удаление модели Theme из админки (admin-interface)
admin.site.unregister(Theme)
# Удаление модели Group из админки
admin.site.unregister(Group)

# Регистрация кастомной модели пользователя в админке
admin.site.register(CustomUser)
# Регистрация модели заявок в админке
admin.site.register(Application)
# Регистрация модели отзывов в админке
admin.site.register(Review)