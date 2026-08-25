from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import traceback
from django.utils import timezone
from datetime import date, time as time_obj

from .models import Cita
from historial.models import registrar
from . import mensajes


# ── Helper de rol / acceso (mismo patrón que _verificar_acceso_prospecto) ────

def _es_admin(user):
    """
    Determina si el usuario tiene privilegios administrativos (Superadmin o
    Administrador). is_superuser se revisa PRIMERO: antes, si el perfil
    existía, su rol ganaba siempre, así que un Superadmin con perfil
    rol='asesor' era tratado como Asesor en este módulo. Mismo criterio
    que usuarios/permisos.py::es_admin().
    """
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.es_admin)


def _qs_citas(user):
    """
    Devuelve el queryset de Cita visible para este usuario.
    Admin/superuser → todas. Asesor → solo las suyas (Cita.asesor == user).
    """
    if _es_admin(user):
        return Cita.objects.all()
    return Cita.objects.filter(asesor=user)


def _verificar_acceso_cita(request, cita):
    """
    Verifica que el usuario autenticado tenga acceso a esta cita.
    Sigue el mismo patrón que _verificar_acceso_prospecto() en
    prospectos/views.py.

    Devuelve (True, None)              → acceso permitido.
    Devuelve (False, JsonResponse 403) → si la petición es AJAX.
    Devuelve (False, redirect seguro)  → si la vista es HTML.

    Uso en cualquier endpoint con cita_id:
        permitido, respuesta_error = _verificar_acceso_cita(request, cita)
        if not permitido:
            return respuesta_error
    """
    if _es_admin(request.user):
        return True, None

    if cita.asesor_id != request.user.id:
        es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if es_ajax:
            return False, JsonResponse(
                {'ok': False, 'error': 'No tienes permiso para acceder a esta cita.'},
                status=403,
            )
        messages.error(request, 'No tienes permiso para acceder a esa cita.')
        return False, redirect('citas:lista')

    return True, None


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

        correo = request.POST.get('correo', '').strip()

        # Asignación automática de asesor (round-robin). El formulario
        # público NUNCA envía ni acepta un asesor_id — el asesor lo
        # decide siempre el backend aquí. Ver asignacion/servicios.py.
        from asignacion.servicios import obtener_asesor_para
        asesor_asignado = obtener_asesor_para(correo)

        cita = Cita.objects.create(
            nombre_cliente    = request.POST.get('nombre', '').strip(),
            apellidos_cliente = request.POST.get('apellidos', '').strip(),
            correo            = correo,
            telefono          = request.POST.get('telefono', '').strip(),
            fecha             = fecha,
            hora              = request.POST.get('hora'),
            motivo            = request.POST.get('motivo', ''),
            motivo_otro       = request.POST.get('motivo_otro', ''),
            comentarios       = request.POST.get('comentarios', ''),
            asesor            = asesor_asignado,
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
    qs_base = _qs_citas(request.user)
    citas = qs_base.order_by('-creada')

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
        'total': qs_base.count(),
        'pendientes': qs_base.filter(estado='pendiente').count(),
        'confirmadas': qs_base.filter(estado='confirmada').count(),
        'completadas': qs_base.filter(estado='completada').count(),
        'canceladas': qs_base.filter(estado='cancelada').count(),
        'es_admin': _es_admin(request.user),
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
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err
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
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    cita = get_object_or_404(Cita, id=cita_id)
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err

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


# ── API JSON: detalle de una cita (desde el dashboard) ───────────────────────
@login_required
def detalle_ajax(request, cita_id):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    cita = get_object_or_404(Cita, id=cita_id)
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err
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

# ── Helper: mantener Prospecto.asesor_asignado sincronizado con Cita.asesor ──
def _sincronizar_prospecto_por_asesor(cita, asesor):
    """
    Se llama cada vez que cambia el asesor de una Cita (asignado o removido).
    - Si se asigna un asesor y no existe Prospecto con ese correo, lo crea.
    - Si se asigna un asesor y ya existe el Prospecto, actualiza su asesor_asignado.
    - Si se quita el asesor (asesor=None), el Prospecto existente pierde su
      asesor_asignado y por lo tanto deja de aparecer en el CRM filtrado de
      ese asesor (no se elimina el registro, solo se desasigna).
    """
    from prospectos.models import Prospecto

    if not cita.correo:
        return None

    prospecto = Prospecto.objects.filter(correo=cita.correo).first()

    if asesor is None:
        if prospecto and prospecto.asesor_asignado_id:
            prospecto.asesor_asignado = None
            prospecto.save(update_fields=['asesor_asignado'])
        return prospecto

    motivo_a_interes = {
        'seguro_vida': 'seguro_vida', 'medico': 'medico', 'auto': 'auto',
        'hogar': 'hogar', 'inversion': 'inversion', 'empresa': 'empresa',
        'otro': 'general',
    }

    if prospecto is None:
        prospecto = Prospecto.objects.create(
            nombre=f'{cita.nombre_cliente} {cita.apellidos_cliente}'.strip(),
            correo=cita.correo,
            telefono=cita.telefono,
            interes=motivo_a_interes.get(cita.motivo, 'general'),
            servicios_interes=motivo_a_interes.get(cita.motivo, 'general'),
            mensaje=cita.comentarios or '',
            estado='nuevo',
            tipo_registro='prospecto',
            asesor_asignado=asesor,
        )
    elif prospecto.asesor_asignado_id != asesor.id:
        prospecto.asesor_asignado = asesor
        prospecto.save(update_fields=['asesor_asignado'])

    return prospecto

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
    es_admin = _es_admin(request.user)
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
    if not _es_admin(request.user):
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
    _sincronizar_prospecto_por_asesor(cita, cita.asesor)

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
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err

    try:
        fecha_str = request.POST.get('fecha', '').strip()
        fecha = date.fromisoformat(fecha_str)

        hora_str = request.POST.get('hora', '').strip()
        partes = hora_str.split(':')
        hora = time_type(int(partes[0]), int(partes[1]))

        motivo = request.POST.get('motivo', '').strip()
        if motivo not in [m[0] for m in Cita.MOTIVO_CHOICES]:
            return JsonResponse({'ok': False, 'error': 'Motivo no válido.'}, status=400)

        estado = request.POST.get('estado', '').strip()
        if estado not in [e[0] for e in Cita.ESTADO_CHOICES]:
            return JsonResponse({'ok': False, 'error': 'Estado no válido.'}, status=400)

        cita.nombre_cliente    = request.POST.get('nombre', '').strip()
        cita.apellidos_cliente = request.POST.get('apellidos', '').strip()
        cita.correo            = request.POST.get('correo', '').strip()
        cita.telefono          = request.POST.get('telefono', '').strip()
        cita.fecha             = fecha
        cita.hora              = hora
        cita.motivo            = motivo
        cita.motivo_otro       = request.POST.get('motivo_otro', '').strip()
        cita.comentarios       = request.POST.get('comentarios', '').strip()
        cita.estado            = estado

        # Asesor: solo administradores pueden asignarlo/cambiarlo desde Editar.
        es_admin = _es_admin(request.user)
        if es_admin and 'asesor_id' in request.POST:
            asesor_id = request.POST.get('asesor_id', '').strip()
            if asesor_id:
                from django.contrib.auth.models import User as UserModel
                cita.asesor = get_object_or_404(UserModel, id=asesor_id, is_active=True)
            else:
                cita.asesor = None

        cita.save()
        _sincronizar_prospecto_por_asesor(cita, cita.asesor)

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
            'estado':         cita.estado,
            'estado_display': cita.get_estado_display(),
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
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err
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


# ── API JSON: eliminar cita vía AJAX (sin redirect, retorna JSON) ────────────
@login_required
def eliminar_ajax(request, cita_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    cita = get_object_or_404(Cita, id=cita_id)
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err
    nombre = f'{cita.nombre_cliente} {cita.apellidos_cliente}'
    cita.delete()
    registrar(
        usuario=request.user,
        accion=f'Cita de {nombre} eliminada',
        modulo='citas',
        objeto_id=cita_id,
        request=request,
    )
    # Contadores actualizados para el frontend
    contadores = {
        'total':       Cita.objects.count(),
        'pendiente':   Cita.objects.filter(estado='pendiente').count(),
        'confirmada':  Cita.objects.filter(estado='confirmada').count(),
        'completada':  Cita.objects.filter(estado='completada').count(),
        'cancelada':   Cita.objects.filter(estado='cancelada').count(),
    }
    return JsonResponse({
        'ok': True,
        'nombre': nombre,
        'contadores': contadores,
    })


# ── API JSON: mensaje generado para una cita (WhatsApp) ──────────────────────
@login_required
def mensaje_generado_ajax(request, cita_id, clave):
    """
    Devuelve el texto ya personalizado de una plantilla de mensaje para esta
    cita de asesoría. Solo genera el texto — el envío por WhatsApp lo hace
    el frontend con la URL wa.me.
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    cita = get_object_or_404(Cita, id=cita_id)
    permitido, err = _verificar_acceso_cita(request, cita)
    if not permitido:
        return err

    texto = mensajes.generar_mensaje(clave, cita)
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Plantilla no encontrada'}, status=404)

    return JsonResponse({'ok': True, 'clave': clave, 'texto': texto})
