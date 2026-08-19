from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',               views.index,               name='index'),
    path('asesor/',        views.index_asesor,        name='asesor'),
    path('asesor/agenda/',      views.agenda_asesor,      name='agenda_asesor'),
    path('asesor/prospectos/',  views.prospectos_asesor,  name='prospectos_asesor'),
    path('kpis/',          views.kpis_ajax,           name='kpis_ajax'),
    path('notificaciones/',views.notificaciones_ajax, name='notificaciones_ajax'),
]