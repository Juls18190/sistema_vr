from django.urls import path
from . import views

app_name = 'asignacion'

urlpatterns = [
    path('estado/ajax/', views.estado_ajax, name='estado_ajax'),
    path('toggle/ajax/', views.toggle_ajax, name='toggle_ajax'),
]
