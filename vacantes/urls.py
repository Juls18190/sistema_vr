from django.urls import path
from . import views

app_name = 'vacantes'

urlpatterns = [
    # Pública
    path('',                                  views.index,        name='index'),
    # Admin
    path('admin/',                            views.lista,        name='lista'),
    path('admin/crear/',                      views.crear,        name='crear'),
    path('admin/<int:vacante_id>/editar/',    views.editar,       name='editar'),
    path('admin/<int:vacante_id>/toggle/',    views.toggle_estado,name='toggle_estado'),
    path('admin/<int:vacante_id>/eliminar/',  views.eliminar,     name='eliminar'),
]