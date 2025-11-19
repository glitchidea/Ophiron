from django.urls import path
from . import views

app_name = 'package_manager'

urlpatterns = [
    path('', views.index_view, name='index'),
    # API endpoints
    path('api/summary/', views.summary_api, name='summary_api'),
    path('api/installed/', views.installed_api, name='installed_api'),
    path('api/detail/<str:manager>/<path:package_name>/', views.detail_api, name='detail_api'),
    path('api/updates/', views.updates_api, name='updates_api'),
]


