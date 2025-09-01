# workorders/admin_urls.py
from django.urls import path
from .views import workorder_unified

urlpatterns = [
    path("workorder/new/", workorder_unified, name="workorders_admin_new"),
    path("workorder/<int:pk>/edit/", workorder_unified, name="workorders_admin_edit"),
]
