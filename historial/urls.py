# historial/urls.py
from django.urls import path
from . import views

app_name = 'historial'

urlpatterns = [
    path('actividad/ajax/', views.actividad_ajax, name='actividad_ajax'),
]
