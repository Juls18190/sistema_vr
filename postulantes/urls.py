from django.urls import path
from . import views

app_name = 'postulantes'

urlpatterns = [
    # ── Públicas ──────────────────────────────────────────────────
    path('crear/', views.crear, name='crear'),
    path('exito/', views.exito, name='exito'),

    # ── Admin ─────────────────────────────────────────────────────
    path('admin/',                            views.lista,               name='lista'),
    path('admin/<int:post_id>/estado/ajax/',  views.cambiar_estado_ajax, name='cambiar_estado_ajax'),
    path('admin/<int:post_id>/eliminar/',     views.eliminar,            name='eliminar'),
]