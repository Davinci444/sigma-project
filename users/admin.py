"""Admin configuration for user profiles."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profiles."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfiles de Zona"


class UserAdmin(BaseUserAdmin):
    """User admin with integrated profile inline."""

    inlines = (UserProfileInline,)


# Re-registramos el User admin para aplicar nuestra versión personalizada
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
