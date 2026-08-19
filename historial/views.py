# historial/views.py
#
# Vista AJAX del módulo Historial con filtros reales de periodo y módulo
# (mismo patrón ya probado en reportes/views.py). Reemplaza el filtrado
# puramente client-side que antes solo ocultaba filas ya renderizadas
# (limitadas a las últimas 15) por una consulta real a PostgreSQL sin ese
# límite, con un resumen por módulo.

from datetime import datetime as _dt, time as _time, timedelta as _timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone as _timezone

from usuarios.permisos import solo_admin
from .models import Historial


def _rango_periodo(periodo):
    """Convierte 'hoy'|'semana'|'mes'|'año'|'' en un datetime de inicio (o None si es 'todo')."""
    hoy = _timezone.now().date()
    if periodo == 'hoy':
        inicio = hoy
    elif periodo == 'semana':
        inicio = hoy - _timedelta(days=hoy.weekday())
    elif periodo == 'mes':
        inicio = hoy.replace(day=1)
    elif periodo == 'año':
        inicio = hoy.replace(month=1, day=1)
    else:
        return None
    return _timezone.make_aware(_dt.combine(inicio, _time.min))


@login_required
@solo_admin
def actividad_ajax(request):
    """
    Devuelve el listado de Historial filtrado por periodo y/o módulo,
    junto con el total y un desglose por módulo. Máximo 200 filas para
    no sobrecargar la respuesta (el total real ya viene en 'resumen').
    """
    qs = Historial.objects.select_related('usuario').all()

    periodo = request.GET.get('periodo', '').strip()
    modulo  = request.GET.get('modulo', '').strip()

    errores = []

    inicio = _rango_periodo(periodo)
    if inicio:
        qs = qs.filter(fecha__gte=inicio)

    if modulo:
        if modulo in dict(Historial.MODULO_CHOICES):
            qs = qs.filter(modulo=modulo)
        else:
            errores.append('Módulo inválido.')

    if errores:
        return JsonResponse({'ok': False, 'error': ' '.join(errores)}, status=400)

    total = qs.count()
    por_modulo = [
        {'modulo': label, 'clave': clave, 'total': qs.filter(modulo=clave).count()}
        for clave, label in Historial.MODULO_CHOICES
    ]

    listado = [
        {
            'usuario':      (h.usuario.get_full_name() or h.usuario.username) if h.usuario else 'Sistema',
            'accion':       h.accion,
            'modulo':       h.modulo,
            'modulo_label': h.get_modulo_display(),
            'fecha':        h.fecha.strftime('%d/%m/%Y %H:%M'),
        }
        for h in qs.order_by('-fecha')[:200]
    ]

    return JsonResponse({
        'ok': True,
        'resumen': {'total': total},
        'por_modulo': por_modulo,
        'listado': listado,
    })
