from django.urls import path
from . import views

app_name = 'dev_packages'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/summary/', views.summary_api, name='summary_api'),
    path('api/installed/', views.installed_api, name='installed_api'),
    path('api/updates/', views.updates_api, name='updates_api'),
    path('api/detail/<str:manager>/<path:name>/', views.detail_api, name='detail_api'),
    path('api/cves/', views.cves_api, name='cves_api'),
    path('api/cves/<str:manager>/<path:name>/', views.package_cves_api, name='package_cves_api'),
]

