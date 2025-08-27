# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Definimos un 'inline' para el perfil
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfiles de Zona'

# Definimos un nuevo User admin que incluye el perfil
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-registramos el User admin para aplicar nuestra versión personalizada
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
