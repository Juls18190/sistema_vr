from django.urls import path
from . import views

app_name = 'postulantes'

urlpatterns = [
    # ── Públicas ──────────────────────────────────────────────────
    path('crear/', views.crear, name='crear'),
    path('exito/', views.exito, name='exito'),
    path('cambiar-estado/<int:id>/', views.cambiar_estado,name='cambiar_estado'),
    # ── Admin ─────────────────────────────────────────────────────
    path('admin/',                            views.lista,               name='lista'),
    path('admin/crear/ajax/',                 views.crear_ajax,          name='crear_ajax'),
    path('admin/<int:post_id>/estado/ajax/',  views.cambiar_estado_ajax, name='cambiar_estado_ajax'),
    path('admin/<int:post_id>/eliminar/',      views.eliminar,            name='eliminar'),
    path('admin/<int:post_id>/eliminar/ajax/', views.eliminar_ajax,       name='eliminar_ajax'),
    path('admin/<int:post_id>/detalle/ajax/',  views.detalle_ajax,        name='detalle_ajax'),
    path('admin/<int:post_id>/nota/ajax/',     views.guardar_nota_ajax,   name='guardar_nota_ajax'),
]