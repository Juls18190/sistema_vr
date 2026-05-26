from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    # ── Públicas ──────────────────────────────────────────────
    path('agendar/',             views.agendar,             name='agendar'),
    path('exito/',               views.exito,               name='exito'),

    # ── Admin (requieren login) ────────────────────────────────
    path('admin/',               views.lista,               name='lista'),
    path('admin/crear/',         views.crear,               name='crear'),
    path('admin/<int:cita_id>/estado/',      views.cambiar_estado,      name='cambiar_estado'),
    path('admin/<int:cita_id>/estado/ajax/', views.cambiar_estado_ajax, name='cambiar_estado_ajax'),
    path('admin/<int:cita_id>/eliminar/',    views.eliminar,            name='eliminar'),
]