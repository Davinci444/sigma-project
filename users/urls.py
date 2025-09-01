"""URL routes for the users application."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DriverViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r"drivers", DriverViewSet)
router.register(r"profiles", UserProfileViewSet)

urlpatterns = [path("", include(router.urls))]
