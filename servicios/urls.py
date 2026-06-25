from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    path('',                                views.index,            name='index'),
    path('crear/ajax/',                     views.crear_ajax,       name='crear_ajax'),
    path('<int:serv_id>/detalle/ajax/',      views.detalle_ajax,     name='detalle_ajax'),
    path('<int:serv_id>/editar/ajax/',       views.editar_ajax,      name='editar_ajax'),
    path('<int:serv_id>/eliminar/ajax/',     views.eliminar_ajax,    name='eliminar_ajax'),
    path('<int:serv_id>/toggle/ajax/',       views.toggle_activo_ajax, name='toggle_activo_ajax'),
]