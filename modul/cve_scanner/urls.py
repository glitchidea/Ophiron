from django.urls import path
from . import views


app_name = "cve_scanner"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("scan/", views.scan_view, name="scan"),
]


