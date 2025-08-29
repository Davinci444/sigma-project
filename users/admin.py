# users/admin.py  (REEMPLAZA COMPLETO)
from django.contrib import admin
from .models import Driver

class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "document_number", "zone", "is_active")
    list_filter = ("is_active", "zone")
    search_fields = ("full_name", "document_number")

# Registro seguro: evita AlreadyRegistered si ya estaba
if Driver not in admin.site._registry:
    admin.site.register(Driver, DriverAdmin)
