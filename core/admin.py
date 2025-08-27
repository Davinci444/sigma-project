# core/admin.py
from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'message', 'seen', 'created_at')
    list_filter = ('alert_type', 'severity', 'seen')