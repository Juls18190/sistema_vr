from django.urls import path
from . import views

app_name = 'prospectos'

urlpatterns = [
    path('',                                    views.index,              name='index'),
    path('nuevo/',                              views.nuevo,              name='nuevo'),
    path('exito/',                              views.exito,              name='exito'),
    path('crear/',                              views.crear,              name='crear'),
    path('<int:prospecto_id>/editar/',          views.editar,             name='editar'),
    path('<int:prospecto_id>/eliminar/',        views.eliminar,           name='eliminar'),
    path('<int:prospecto_id>/expediente/',      views.expediente,         name='expediente'),
    path('<int:prospecto_id>/expediente/ajax/', views.expediente_ajax,    name='expediente_ajax'),
    path('<int:prospecto_id>/seguimiento/',     views.agregar_seguimiento,name='agregar_seguimiento'),
    path('<int:prospecto_id>/convertir/',       views.convertir,          name='convertir'),
    path('<int:prospecto_id>/estado/ajax/',     views.cambiar_estado_ajax,name='cambiar_estado_ajax'),
    path('<int:prospecto_id>/mensaje/<str:clave>/ajax/', views.mensaje_generado_ajax, name='mensaje_generado_ajax'),
]