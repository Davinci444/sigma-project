# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload-fuel-file/', views.upload_fuel_file_view, name='upload_fuel_file'),
]
