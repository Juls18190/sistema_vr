from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import TareaAgenda
from citas.models import Cita
from usuarios.permisos import es_admin
from historial.models import registrar


def _mes_valido(anio, mes):
    """Recorta año/mes a un rango razonable y evita ValueError de calendar."""
    try:
        anio = int(anio)
        mes  = int(mes)
    except (TypeError, ValueError):
        return None, None
    if mes < 1 or mes > 12:
        return None, None
    return anio, mes


@login_required
def calendario_ajax(request):
    """
    Devuelve, para un mes dado, las Citas y TareaAgenda combinadas.

    - Asesor (no admin): siempre ve solo lo suyo (Cita.asesor=usuario,
      TareaAgenda.usuario=usuario) — el parámetro ?asesor_id se ignora
      para cualquier no-admin, el backend es la autoridad.
    - Admin/Superadmin: puede pedir ?asesor_id=<id> para ver a un asesor
      en particular, o sin ese parámetro (o "todos") para ver a todos los
      asesores combinados, cada uno con un color propio.
    """
    anio, mes = _mes_valido(request.GET.get('anio'), request.GET.get('mes'))
    if anio is None:
        return JsonResponse({'ok': False, 'error': 'Año/mes inválido.'}, status=400)

    admin = es_admin(request.user)
    asesor_id = request.GET.get('asesor_id', '').strip()

    if admin:
        if asesor_id and asesor_id != 'todos':
            usuarios_ids = [asesor_id]
        else:
            usuarios_ids = None  # None == todos
    else:
        usuarios_ids = [request.user.id]

    citas_qs = Cita.objects.filter(fecha__year=anio, fecha__month=mes).select_related('asesor')
    tareas_qs = TareaAgenda.objects.filter(fecha__year=anio, fecha__month=mes).select_related('usuario')

    if usuarios_ids is not None:
        citas_qs = citas_qs.filter(asesor_id__in=usuarios_ids)
        tareas_qs = tareas_qs.filter(usuario_id__in=usuarios_ids)

    # Paleta simple para distinguir asesores cuando el admin ve "todos".
    # Se asigna de forma estable según el id del usuario (mismo asesor
    # siempre el mismo color dentro de una misma carga).
    paleta = ['#1560BD', '#7c3aed', '#0d9488', '#c2410c', '#be185d', '#4d7c0f', '#a16207']

    def color_de(user_id):
        return paleta[user_id % len(paleta)]

    eventos = []
    for c in citas_qs:
        eventos.append({
            'tipo':       'cita',
            'id':         c.id,
            'fecha':      c.fecha.isoformat(),
            'hora':       c.hora.strftime('%H:%M') if c.hora else None,
            'titulo':     f'{c.nombre_cliente} {c.apellidos_cliente}',
            'subtitulo':  c.get_motivo_display(),
            'estado':     c.estado,
            'asesor_id':  c.asesor_id,
            'asesor_nombre': (c.asesor.get_full_name() or c.asesor.username) if c.asesor else 'Sin asignar',
            'color':      color_de(c.asesor_id) if c.asesor_id else '#94a3b8',
        })
    for t in tareas_qs:
        eventos.append({
            'tipo':       'tarea',
            'id':         t.id,
            'fecha':      t.fecha.isoformat(),
            'hora':       t.hora.strftime('%H:%M') if t.hora else None,
            'titulo':     t.texto,
            'subtitulo':  '',
            'completada': t.completada,
            'asesor_id':  t.usuario_id,
            'asesor_nombre': t.usuario.get_full_name() or t.usuario.username,
            'color':      color_de(t.usuario_id),
            'editable':   (t.usuario_id == request.user.id),
        })

    asesores = []
    if admin:
        asesores = [
            {'id': u.id, 'nombre': u.get_full_name() or u.username, 'color': color_de(u.id)}
            for u in User.objects.filter(perfil__rol='asesor', is_active=True).order_by('first_name', 'username')
        ]

    return JsonResponse({
        'ok': True,
        'anio': anio,
        'mes': mes,
        'eventos': eventos,
        'es_admin': admin,
        'asesores': asesores,
    })


@login_required
@require_POST
def crear_tarea_ajax(request):
    """Crea una tarea propia. Siempre queda asignada a request.user —
    nadie puede crear una tarea "a nombre de" otro usuario desde aquí."""
    fecha = request.POST.get('fecha', '').strip()
    hora  = request.POST.get('hora', '').strip() or None
    texto = request.POST.get('texto', '').strip()

    if not fecha:
        return JsonResponse({'ok': False, 'error': 'La fecha es obligatoria.'}, status=400)
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Escribe qué tienes que hacer.'}, status=400)

    tarea = TareaAgenda.objects.create(
        usuario=request.user,
        fecha=fecha,
        hora=hora,
        texto=texto,
    )
    registrar(usuario=request.user, accion=f'Agregó tarea de agenda: "{texto[:60]}"', modulo='agenda', objeto_id=tarea.id, request=request)

    return JsonResponse({'ok': True, 'id': tarea.id})


def _obtener_tarea_propia(request, tarea_id):
    """Devuelve la tarea si pertenece al usuario, o None. Un admin no puede
    editar/eliminar tareas de un asesor: son notas personales, no un
    registro administrable como Citas o Prospectos."""
    tarea = get_object_or_404(TareaAgenda, id=tarea_id)
    if tarea.usuario_id != request.user.id:
        return None
    return tarea


@login_required
@require_POST
def editar_tarea_ajax(request, tarea_id):
    tarea = _obtener_tarea_propia(request, tarea_id)
    if tarea is None:
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para modificar esta tarea.'}, status=403)

    fecha = request.POST.get('fecha', '').strip()
    hora  = request.POST.get('hora', '').strip() or None
    texto = request.POST.get('texto', '').strip()

    if not fecha or not texto:
        return JsonResponse({'ok': False, 'error': 'Fecha y texto son obligatorios.'}, status=400)

    tarea.fecha = fecha
    tarea.hora  = hora
    tarea.texto = texto
    tarea.save(update_fields=['fecha', 'hora', 'texto', 'actualizada'])

    return JsonResponse({'ok': True})


@login_required
@require_POST
def completar_tarea_ajax(request, tarea_id):
    tarea = _obtener_tarea_propia(request, tarea_id)
    if tarea is None:
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para modificar esta tarea.'}, status=403)

    tarea.completada = not tarea.completada
    tarea.save(update_fields=['completada', 'actualizada'])

    return JsonResponse({'ok': True, 'completada': tarea.completada})


@login_required
@require_POST
def eliminar_tarea_ajax(request, tarea_id):
    tarea = _obtener_tarea_propia(request, tarea_id)
    if tarea is None:
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para eliminar esta tarea.'}, status=403)

    tarea.delete()
    return JsonResponse({'ok': True})
