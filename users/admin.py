"""Admin configuration for user profiles and drivers."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, Driver


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profiles."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfiles de Zona"


class UserAdmin(BaseUserAdmin):
    """User admin with integrated profile inline."""
    inlines = (UserProfileInline,)


# Re-registrar User con el inline de perfil
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "document_number", "zone", "active", "created_at")
    list_filter = ("active", "zone")
    search_fields = ("full_name", "document_number", "email", "phone")
    list_per_page = 25
