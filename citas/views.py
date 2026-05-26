from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date

from .models import Cita
from historial.models import registrar


# ── Vista pública: formulario para agendar cita (desde el sitio) ──────────────
def agendar(request):
    if request.method == 'POST':
        # Validación de fecha: no puede ser en el pasado
        fecha_str = request.POST.get('fecha', '')
        try:
            fecha = date.fromisoformat(fecha_str)
            if fecha < date.today():
                return render(request, 'citas/formulario.html', {
                    'error': 'La fecha de la cita no puede ser anterior a hoy.',
                    'post': request.POST,
                })
        except (ValueError, TypeError):
            return render(request, 'citas/formulario.html', {
                'error': 'Por favor ingresa una fecha válida.',
                'post': request.POST,
            })

        cita = Cita.objects.create(
            nombre_cliente    = request.POST.get('nombre', '').strip(),
            apellidos_cliente = request.POST.get('apellidos', '').strip(),
            correo            = request.POST.get('correo', '').strip(),
            telefono          = request.POST.get('telefono', '').strip(),
            fecha             = fecha,
            hora              = request.POST.get('hora'),
            motivo            = request.POST.get('motivo', ''),
            motivo_otro       = request.POST.get('motivo_otro', ''),
            comentarios       = request.POST.get('comentarios', ''),
        )
        # Registrar en historial (sin usuario porque es público)
        registrar(
            usuario=None,
            accion=f'Nueva cita agendada por {cita.nombre_cliente} {cita.apellidos_cliente} para {cita.fecha}',
            modulo='citas',
            objeto_id=cita.id,
            request=request,
        )
        return redirect('citas:exito')
    return render(request, 'citas/formulario.html')


def exito(request):
    return render(request, 'citas/exito.html')


# ── Vista admin: lista todas las citas con filtros ───────────────────────────
@login_required
def lista(request):
    citas = Cita.objects.all().order_by('-creada')

    estado = request.GET.get('estado', '')
    if estado:
        citas = citas.filter(estado=estado)

    busqueda = request.GET.get('q', '')
    if busqueda:
        citas = citas.filter(nombre_cliente__icontains=busqueda) | \
                citas.filter(apellidos_cliente__icontains=busqueda)

    contexto = {
        'citas': citas,
        'estado_filtro': estado,
        'busqueda': busqueda,
        'total': Cita.objects.count(),
        'pendientes': Cita.objects.filter(estado='pendiente').count(),
        'confirmadas': Cita.objects.filter(estado='confirmada').count(),
        'completadas': Cita.objects.filter(estado='completada').count(),
        'canceladas': Cita.objects.filter(estado='cancelada').count(),
    }
    return render(request, 'citas/lista.html', contexto)


# ── Vista admin: crear cita desde el dashboard ───────────────────────────────
@login_required
def crear(request):
    if request.method == 'POST':
        try:
            fecha_str = request.POST.get('fecha', '')
            fecha = date.fromisoformat(fecha_str)
            cita = Cita.objects.create(
                nombre_cliente    = request.POST.get('nombre', '').strip(),
                apellidos_cliente = request.POST.get('apellidos', '').strip(),
                correo            = request.POST.get('correo', '').strip(),
                telefono          = request.POST.get('telefono', '').strip(),
                fecha             = fecha,
                hora              = request.POST.get('hora'),
                motivo            = request.POST.get('motivo', ''),
                motivo_otro       = request.POST.get('motivo_otro', ''),
                comentarios       = request.POST.get('comentarios', ''),
                estado            = 'pendiente',
                asesor            = request.user if request.POST.get('asignar_a_mi') else None,
            )
            registrar(
                usuario=request.user,
                accion=f'Cita creada para {cita.nombre_cliente} {cita.apellidos_cliente} ({cita.fecha})',
                modulo='citas',
                objeto_id=cita.id,
                request=request,
            )
            messages.success(request, 'Cita agendada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {e}')
        return redirect('citas:lista')
    return redirect('citas:lista')


# ── Vista admin: cambiar estado de una cita ──────────────────────────────────
@login_required
def cambiar_estado(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Cita.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            estado_anterior = cita.estado
            cita.estado = nuevo_estado
            cita.save()
            registrar(
                usuario=request.user,
                accion=f'Cita #{cita_id} cambió de "{estado_anterior}" a "{nuevo_estado}"',
                modulo='citas',
                objeto_id=cita_id,
                request=request,
            )
            messages.success(request, f'Estado actualizado a "{cita.get_estado_display()}".')
        else:
            messages.error(request, 'Estado no válido.')
    return redirect('citas:lista')


# ── API JSON: cambiar estado vía AJAX (desde el dashboard) ──────────────────
@login_required
def cambiar_estado_ajax(request, cita_id):
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id=cita_id)
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Cita.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            estado_anterior = cita.estado
            cita.estado = nuevo_estado
            cita.save()
            registrar(
                usuario=request.user,
                accion=f'Cita #{cita_id} cambió de "{estado_anterior}" a "{nuevo_estado}"',
                modulo='citas',
                objeto_id=cita_id,
                request=request,
            )
            return JsonResponse({'ok': True, 'estado': cita.estado, 'estado_display': cita.get_estado_display()})
        return JsonResponse({'ok': False, 'error': 'Estado no válido'}, status=400)
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# ── Vista admin: eliminar cita ────────────────────────────────────────────────
@login_required
def eliminar(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if request.method == 'POST':
        nombre = f'{cita.nombre_cliente} {cita.apellidos_cliente}'
        cita.delete()
        registrar(
            usuario=request.user,
            accion=f'Cita de {nombre} eliminada',
            modulo='citas',
            objeto_id=cita_id,
            request=request,
        )
        messages.success(request, 'Cita eliminada.')
    return redirect('citas:lista')
