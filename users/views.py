"""Viewsets for the users application."""

from rest_framework import viewsets, filters

from .models import Driver, UserProfile
from .serializers import DriverSerializer, UserProfileSerializer


class DriverViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing drivers."""

    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name", "document_number"]


class UserProfileViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing user profiles."""

    queryset = UserProfile.objects.select_related("user")
    serializer_class = UserProfileSerializer
