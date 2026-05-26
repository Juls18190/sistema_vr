from django.urls import path
from . import views

app_name = 'prospectos'

urlpatterns = [
    path('',                          views.index,    name='index'),
    path('nuevo/',                    views.nuevo,    name='nuevo'),
    path('exito/',                    views.exito,    name='exito'),
    path('crear/',                    views.crear,    name='crear'),
    path('<int:prospecto_id>/editar/',  views.editar,   name='editar'),
    path('<int:prospecto_id>/eliminar/',views.eliminar, name='eliminar'),
]