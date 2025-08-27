# users/models.py
from django.db import models
from django.contrib.auth.models import User
from core.models import Zone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zona Asignada")

    def __str__(self):
        return self.user.username
