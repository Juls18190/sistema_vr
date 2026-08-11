from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [

    # ─────────────────────────────────────────────
    # VISTAS PÚBLICAS
    # ─────────────────────────────────────────────
    path('agendar/', views.agendar, name='agendar'),
    path('exito/', views.exito, name='exito'),


    # ─────────────────────────────────────────────
    # ADMINISTRACIÓN DE CITAS
    # ─────────────────────────────────────────────
    path('admin/', views.lista, name='lista'),
    path('admin/crear/', views.crear, name='crear'),
    path('admin/crear/ajax/', views.crear_ajax, name='crear_ajax'),

    # Estado
    path(
        'admin/<int:cita_id>/estado/',
        views.cambiar_estado,
        name='cambiar_estado'
    ),
    path(
        'admin/<int:cita_id>/estado/ajax/',
        views.cambiar_estado_ajax,
        name='cambiar_estado_ajax'
    ),

    # Asesor
    path(
        'admin/<int:cita_id>/asignar/ajax/',
        views.asignar_asesor_ajax,
        name='asignar_asesor_ajax'
    ),

    # Cita → Prospecto
    path(
        'admin/<int:cita_id>/asignar-prospecto/ajax/',
        views.asignar_y_crear_prospecto_ajax,
        name='asignar_y_crear_prospecto_ajax'
    ),

    # Detalle y edición
    path(
        'admin/<int:cita_id>/detalle/ajax/',
        views.detalle_ajax,
        name='detalle_ajax'
    ),
    path(
        'admin/<int:cita_id>/editar/ajax/',
        views.editar_ajax,
        name='editar_ajax'
    ),

    # Eliminación
    path(
        'admin/<int:cita_id>/eliminar/',
        views.eliminar,
        name='eliminar'
    ),
]