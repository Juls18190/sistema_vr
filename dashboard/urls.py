from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',      views.index,     name='index'),
    path('kpis/', views.kpis_ajax, name='kpis_ajax'),
]