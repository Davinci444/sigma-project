"""Models for user profiles and drivers."""

from django.db import models
from django.contrib.auth.models import User
from core.models import Zone


class UserProfile(models.Model):
    """Extends the default user with an assigned zone."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    zone = models.ForeignKey(
        Zone, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zona Asignada"
    )

    def __str__(self) -> str:
        return self.user.username


class Driver(models.Model):
    """Conductor usado para asignarlo en órdenes de trabajo."""

    full_name = models.CharField("Nombre completo", max_length=150)
    document_number = models.CharField("Número de documento", max_length=50, unique=True)
    zone = models.CharField("Zona", max_length=100, blank=True, null=True)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ["full_name"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.document_number})"
