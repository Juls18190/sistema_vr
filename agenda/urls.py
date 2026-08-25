from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('calendario/ajax/',            views.calendario_ajax,     name='calendario_ajax'),
    path('tarea/crear/ajax/',           views.crear_tarea_ajax,    name='crear_tarea_ajax'),
    path('tarea/<int:tarea_id>/editar/ajax/',     views.editar_tarea_ajax,     name='editar_tarea_ajax'),
    path('tarea/<int:tarea_id>/completar/ajax/',  views.completar_tarea_ajax,  name='completar_tarea_ajax'),
    path('tarea/<int:tarea_id>/eliminar/ajax/',   views.eliminar_tarea_ajax,   name='eliminar_tarea_ajax'),
]
