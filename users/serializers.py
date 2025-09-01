"""Serializers for the users application."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Driver, UserProfile


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver objects."""

    class Meta:
        model = Driver
        fields = ["id", "full_name", "document_number", "zone", "is_active"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile objects."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = UserProfile
        fields = ["id", "user", "zone"]
