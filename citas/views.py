from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import traceback
from django.utils import timezone
from datetime import date, time as time_obj

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


# ── API JSON: detalle de una cita (desde el dashboard) ───────────────────────
@login_required
def detalle_ajax(request, cita_id):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    cita = get_object_or_404(Cita, id=cita_id)
    return JsonResponse({
        'ok':               True,
        'id':               cita.id,
        'nombre_cliente':   cita.nombre_cliente,
        'apellidos_cliente':cita.apellidos_cliente,
        'correo':           cita.correo,
        'telefono':         cita.telefono,
        'fecha':            str(cita.fecha),
        'hora':             str(cita.hora),
        'motivo':           cita.motivo,
        'motivo_display':   cita.get_motivo_display(),
        'motivo_otro':      cita.motivo_otro or '',
        'comentarios':      cita.comentarios or '',
        'estado':           cita.estado,
        'estado_display':   cita.get_estado_display(),
        'asesor':           cita.asesor.get_full_name() or cita.asesor.username if cita.asesor else '',
        'asesor_id':        cita.asesor.id if cita.asesor else None,
        'creada':           timezone.localtime(cita.creada).strftime('%d/%m/%Y %H:%M'),
    })
    
    # ── API JSON: crear cita desde el dashboard ───────────────────────────────────
@login_required
def crear_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    try:
        # Convertir fecha: str → datetime.date
        fecha_str = request.POST.get('fecha', '').strip()
        if not fecha_str:
            return JsonResponse({'ok': False, 'error': 'La fecha es obligatoria.'}, status=400)
        fecha = date.fromisoformat(fecha_str)
        if fecha < date.today():
            return JsonResponse({'ok': False, 'error': 'La fecha no puede ser anterior a hoy.'}, status=400)

        # Convertir hora: str → datetime.time
        # TimeField espera un objeto time, no un string.
        # Si se le pasa un string, create() lo guarda pero el objeto en memoria
        # conserva el string original — por eso .strftime() falla.
        from datetime import time as time_type
        hora_str = request.POST.get('hora', '').strip()
        if not hora_str:
            return JsonResponse({'ok': False, 'error': 'La hora es obligatoria.'}, status=400)
        partes = hora_str.split(':')
        hora = time_type(int(partes[0]), int(partes[1]))

        cita = Cita.objects.create(
            nombre_cliente    = request.POST.get('nombre', '').strip(),
            apellidos_cliente = request.POST.get('apellidos', '').strip(),
            correo            = request.POST.get('correo', '').strip(),
            telefono          = request.POST.get('telefono', '').strip(),
            fecha             = fecha,
            hora              = hora,          # ← ya es datetime.time
            motivo            = request.POST.get('motivo', ''),
            motivo_otro       = request.POST.get('motivo_otro', ''),
            comentarios       = request.POST.get('comentarios', ''),
            estado            = 'pendiente',
            asesor            = request.user,
        )
        registrar(
            usuario=request.user,
            accion=f'Cita creada desde dashboard para {cita.nombre_cliente} {cita.apellidos_cliente} ({cita.fecha})',
            modulo='citas',
            objeto_id=cita.id,
            request=request,
        )
        return JsonResponse({
            'ok':                True,
            'id':                cita.id,
            'nombre_cliente':    cita.nombre_cliente,
            'apellidos_cliente': cita.apellidos_cliente,
            'correo':            cita.correo,
            'fecha':             str(cita.fecha),
            'hora':              cita.hora.strftime('%H:%M'),  # ← ahora sí es time
            'motivo_display':    cita.get_motivo_display(),
            'estado':            cita.estado,
            'estado_display':    cita.get_estado_display(),
            'total':             Cita.objects.count(),
            'pendientes':        Cita.objects.filter(estado='pendiente').count(),
        })

    except (ValueError, IndexError):
        return JsonResponse({'ok': False, 'error': 'Fecha u hora con formato inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

# ── API JSON: flujo completo Cita → Prospecto ────────────────────────────────
@login_required
def asignar_y_crear_prospecto_ajax(request, cita_id):
    """
    Un solo clic ejecuta el flujo completo:
    1. Asigna el asesor a la cita.
    2. Crea el Prospecto (o recupera el existente por correo).
    3. Copia el motivo de la cita a servicios_interes del prospecto.
    4. Copia los comentarios de la cita al prospecto.
    5. Crea el primer seguimiento automático si el prospecto es nuevo.
    6. Registra ambas acciones en Historial.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    from django.contrib.auth.models import User as UserModel
    from prospectos.models import Prospecto, SeguimientoProspecto

    # ── Permisos ──────────────────────────────────────────────────────────────
    try:
        es_admin = request.user.perfil.es_admin
    except Exception:
        es_admin = request.user.is_superuser
    if not es_admin:
        return JsonResponse({'ok': False, 'error': 'Sin permisos de administrador.'}, status=403)

    cita = get_object_or_404(Cita, id=cita_id)

    # ── 1. Asesor ─────────────────────────────────────────────────────────────
    asesor_id = request.POST.get('asesor_id', '').strip()
    if not asesor_id:
        return JsonResponse({'ok': False, 'error': 'Debes seleccionar un asesor.'}, status=400)

    asesor = get_object_or_404(UserModel, id=asesor_id, is_active=True)
    nombre_asesor = asesor.get_full_name() or asesor.username

    cita.asesor = asesor
    cita.save(update_fields=['asesor'])

    registrar(
        usuario=request.user,
        accion=f'Asesor "{nombre_asesor}" asignado a cita #{cita_id} '
               f'({cita.nombre_cliente} {cita.apellidos_cliente})',
        modulo='citas',
        objeto_id=cita_id,
        request=request,
    )

    # ── 2. Mapeo motivo → servicios_interes (CSV) ─────────────────────────────
    # Cita.MOTIVO_CHOICES y Prospecto.INTERES_CHOICES comparten 6 de 7 valores.
    # 'otro' no existe en INTERES_CHOICES → se mapea a 'general'.
    motivo_a_interes = {
        'seguro_vida': 'seguro_vida',
        'medico':      'medico',
        'auto':        'auto',
        'hogar':       'hogar',
        'inversion':   'inversion',
        'empresa':     'empresa',
        'otro':        'general',
    }
    servicios = motivo_a_interes.get(cita.motivo, 'general')

    # ── 3. Crear o recuperar Prospecto por correo ─────────────────────────────
    prospecto, creado = Prospecto.objects.get_or_create(
        correo=cita.correo,
        defaults={
            'nombre':            f'{cita.nombre_cliente} {cita.apellidos_cliente}'.strip(),
            'telefono':          cita.telefono,
            'interes':           servicios,
            'servicios_interes': servicios,
            'mensaje':           cita.comentarios or '',
            'estado':            'nuevo',
            'tipo_registro':     'prospecto',
            'asesor_asignado':   asesor,
        }
    )

    if not creado:
        # Prospecto existente: actualizar asesor y servicios si estaban vacíos
        campos_actualizar = ['asesor_asignado']
        prospecto.asesor_asignado = asesor
        if not prospecto.servicios_interes:
            prospecto.servicios_interes = servicios
            campos_actualizar.append('servicios_interes')
        prospecto.save(update_fields=campos_actualizar)

    # ── 4. Primer seguimiento automático (solo si el prospecto es nuevo) ───────
    if creado:
        motivo_label = dict(cita.MOTIVO_CHOICES).get(cita.motivo, cita.motivo)
        comentario_seg = (
            f'Prospecto creado automáticamente desde cita #{cita_id}.\n'
            f'Motivo: {motivo_label}.'
        )
        if cita.comentarios:
            comentario_seg += f'\nComentarios de la cita: {cita.comentarios}'

        SeguimientoProspecto.objects.create(
            prospecto  = prospecto,
            asesor     = asesor,
            comentario = comentario_seg,
        )

    registrar(
        usuario=request.user,
        accion=(
            f'Prospecto creado automáticamente desde cita #{cita_id}: '
            f'{prospecto.nombre} ({prospecto.correo})'
            if creado else
            f'Prospecto #{prospecto.id} ({prospecto.nombre}) '
            f'actualizado desde cita #{cita_id} — asesor: {nombre_asesor}'
        ),
        modulo='prospectos',
        objeto_id=prospecto.id,
        request=request,
    )

    return JsonResponse({
        'ok':               True,
        'asesor_id':        asesor.id,
        'asesor_nombre':    nombre_asesor,
        'prospecto_id':     prospecto.id,
        'prospecto_nuevo':  creado,
        'prospecto_nombre': prospecto.nombre,
        'prospectos_total': Prospecto.objects.count(),
        'prospectos_nuevos': Prospecto.objects.filter(estado='nuevo').count(),
    })

# ── API JSON: asignar asesor a una cita ──────────────────────────────────────
@login_required
def asignar_asesor_ajax(request, cita_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    # Solo admins pueden asignar asesores
    try:
        if not request.user.perfil.es_admin:
            return JsonResponse({'ok': False, 'error': 'Sin permisos.'}, status=403)
    except Exception:
        if not request.user.is_superuser:
            return JsonResponse({'ok': False, 'error': 'Sin permisos.'}, status=403)

    cita = get_object_or_404(Cita, id=cita_id)
    asesor_id = request.POST.get('asesor_id', '').strip()

    if asesor_id:
        from django.contrib.auth.models import User as UserModel
        asesor = get_object_or_404(UserModel, id=asesor_id, is_active=True)
        nombre_asesor = asesor.get_full_name() or asesor.username
        cita.asesor = asesor
    else:
        nombre_asesor = None
        cita.asesor = None

    cita.save(update_fields=['asesor'])

    registrar(
        usuario=request.user,
        accion=f'Asesor {"asignado: " + nombre_asesor if nombre_asesor else "removido"} en cita #{cita_id} ({cita.nombre_cliente} {cita.apellidos_cliente})',
        modulo='citas',
        objeto_id=cita_id,
        request=request,
    )

    return JsonResponse({
        'ok':           True,
        'asesor_id':    cita.asesor.id if cita.asesor else None,
        'asesor_nombre': nombre_asesor or '',
    })


# ── API JSON: editar una cita ─────────────────────────────────────────────────
@login_required
def editar_ajax(request, cita_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    from datetime import time as time_type
    cita = get_object_or_404(Cita, id=cita_id)

    try:
        fecha_str = request.POST.get('fecha', '').strip()
        fecha = date.fromisoformat(fecha_str)

        hora_str = request.POST.get('hora', '').strip()
        partes = hora_str.split(':')
        hora = time_type(int(partes[0]), int(partes[1]))

        motivo = request.POST.get('motivo', '').strip()
        if motivo not in [m[0] for m in Cita.MOTIVO_CHOICES]:
            return JsonResponse({'ok': False, 'error': 'Motivo no válido.'}, status=400)

        cita.nombre_cliente    = request.POST.get('nombre', '').strip()
        cita.apellidos_cliente = request.POST.get('apellidos', '').strip()
        cita.correo            = request.POST.get('correo', '').strip()
        cita.telefono          = request.POST.get('telefono', '').strip()
        cita.fecha             = fecha
        cita.hora              = hora
        cita.motivo            = motivo
        cita.motivo_otro       = request.POST.get('motivo_otro', '').strip()
        cita.comentarios       = request.POST.get('comentarios', '').strip()

        # Asesor: solo administradores pueden asignarlo/cambiarlo desde Editar.
        try:
            es_admin = request.user.perfil.es_admin
        except Exception:
            es_admin = request.user.is_superuser
        if es_admin and 'asesor_id' in request.POST:
            asesor_id = request.POST.get('asesor_id', '').strip()
            if asesor_id:
                from django.contrib.auth.models import User as UserModel
                cita.asesor = get_object_or_404(UserModel, id=asesor_id, is_active=True)
            else:
                cita.asesor = None

        cita.save()

        registrar(
            usuario=request.user,
            accion=f'Cita #{cita_id} editada por {request.user.get_full_name() or request.user.username}',
            modulo='citas',
            objeto_id=cita_id,
            request=request,
        )

        return JsonResponse({
            'ok':             True,
            'id':             cita.id,
            'nombre_cliente': cita.nombre_cliente,
            'apellidos_cliente': cita.apellidos_cliente,
            'correo':         cita.correo,
            'fecha':          str(cita.fecha),
            'hora':           cita.hora.strftime('%H:%M'),
            'motivo_display': cita.get_motivo_display(),
            'asesor_nombre':  (cita.asesor.get_full_name() or cita.asesor.username) if cita.asesor else '',
        })
    except (ValueError, IndexError):
        return JsonResponse({'ok': False, 'error': 'Fecha u hora con formato inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


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