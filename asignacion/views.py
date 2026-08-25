# asignacion/views.py
#
# Configuración de la asignación automática, gestionada desde el Dashboard
# existente. Mismo criterio de permisos que el resto del sistema
# administrativo: @login_required + @solo_admin (usuarios/permisos.py),
# es decir, is_superuser o rol='admin' — igual que cualquier otra vista
# de configuración del Dashboard, sin inventar un nivel de acceso nuevo.

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from historial.models import registrar
from usuarios.permisos import solo_admin

from .models import ConfiguracionAsignacion
from .servicios import _asesores_activos_ordenados, _siguiente_asesor


@login_required
@solo_admin
def estado_ajax(request):
    """GET: devuelve el estado actual (activo, próximo asesor, participantes)."""
    config = ConfiguracionAsignacion.obtener()
    asesores = list(_asesores_activos_ordenados())
    siguiente = _siguiente_asesor(config, asesores)

    return JsonResponse({
        'ok': True,
        'activo': config.activo,
        'proximo_asesor_id': siguiente.id if siguiente else None,
        'proximo_asesor_nombre': (
            (siguiente.get_full_name() or siguiente.username) if siguiente else ''
        ),
        'asesores_participantes': [
            {'id': a.id, 'nombre': a.get_full_name() or a.username}
            for a in asesores
        ],
    })


@login_required
@solo_admin
def toggle_ajax(request):
    """POST: activa/desactiva la asignación automática."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    activo = request.POST.get('activo', '').strip() == '1'
    config = ConfiguracionAsignacion.obtener()
    config.activo = activo
    config.save(update_fields=['activo', 'actualizado'])

    registrar(
        usuario=request.user,
        accion=f'Asignación automática de citas {"activada" if activo else "desactivada"}',
        modulo='citas',
        objeto_id=None,
        request=request,
    )

    return JsonResponse({'ok': True, 'activo': config.activo})
