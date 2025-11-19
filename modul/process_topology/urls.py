from django.urls import path
from . import views

app_name = 'process_topology'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/data/', views.get_topology_data, name='data'),
    path('api/refresh/', views.refresh_topology, name='refresh'),
]
