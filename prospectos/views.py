from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Prospecto, SeguimientoProspecto
from .forms  import ProspectoForm, ProspectoPublicoForm, SeguimientoForm
from . import mensajes
from historial.models import registrar

# ── Helper de rol ─────────────────────────────────────────────────────────────

def _rol(user):
    """
    Devuelve (es_admin, qs_base) donde qs_base es el queryset
    de prospectos visible para este usuario.
    Regla:
      - Admin / superuser → todos los prospectos.
      - Asesor            → solo los asignados a él.

    IMPORTANTE: is_superuser se revisa PRIMERO, sin importar lo que diga
    el perfil. Antes se hacía al revés (perfil.es_admin ganaba si el
    perfil existía), lo que causaba que un Superadmin cuyo PerfilUsuario
    tuviera rol='asesor' fuera tratado como Asesor en todo este módulo
    (viendo "No tienes permiso" al intentar editar prospectos que no
    fueran suyos). Mismo criterio que usuarios/permisos.py::es_admin().
    """
    if user.is_superuser:
        es_admin = True
    else:
        perfil   = getattr(user, 'perfil', None)
        es_admin = bool(perfil and perfil.es_admin)
    qs_base  = (
        Prospecto.objects.all()
        if es_admin
        else Prospecto.objects.filter(asesor_asignado=user)
    )
    return es_admin, qs_base


def _verificar_acceso_prospecto(request, prospecto):
    """
    Verifica que el usuario autenticado tenga acceso a este prospecto.

    Devuelve (True, None)                → acceso permitido.
    Devuelve (False, JsonResponse 403)   → si la vista es AJAX.
    Devuelve (False, redirect seguro)    → si la vista es HTML.

    Uso en cualquier endpoint:
        permitido, respuesta_error = _verificar_acceso_prospecto(request, prospecto)
        if not permitido:
            return respuesta_error
    """
    es_admin, _ = _rol(request.user)
    if es_admin:
        return True, None

    # Asesor: el prospecto debe estar asignado a él
    if prospecto.asesor_asignado_id != request.user.id:
        es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if es_ajax:
            return False, JsonResponse(
                {'ok': False, 'error': 'No tienes permiso para acceder a este prospecto.'},
                status=403,
            )
        messages.error(request, 'No tienes permiso para acceder a ese prospecto.')
        return False, redirect('prospectos:index')

    return True, None


# ── Vista pública ─────────────────────────────────────────────────────────────

def nuevo(request):
    """Formulario de contacto público del sitio — sin autenticación."""
    if request.method == 'POST':
        form = ProspectoPublicoForm(request.POST)
        if form.is_valid():
            p = form.save()
            registrar(
                usuario=None,
                accion=f'Nuevo prospecto: {p.nombre} — interés en {p.get_interes_display()}',
                modulo='prospectos',
                objeto_id=p.id,
                request=request,
            )
            return redirect('prospectos:exito')
    else:
        form = ProspectoPublicoForm()
    return render(request, 'prospectos/formulario.html', {'form': form})


def exito(request):
    return render(request, 'prospectos/exito.html')


# ── Panel admin ───────────────────────────────────────────────────────────────

@login_required
def index(request):
    """Lista de prospectos — filtrada por rol."""
    es_admin, qs_base = _rol(request.user)

    estado_filtro = request.GET.get('estado', '')
    busqueda      = request.GET.get('q', '')

    qs = qs_base.select_related('asesor_asignado')
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)
    if busqueda:
        qs = qs.filter(nombre__icontains=busqueda) | qs.filter(correo__icontains=busqueda)

    contexto = {
        'prospectos':    qs.order_by('-fecha'),
        'total':         qs_base.count(),
        'nuevos':        qs_base.filter(estado='nuevo').count(),
        'contactados':   qs_base.filter(estado='contactado').count(),
        'convertidos':   qs_base.filter(estado='convertido').count(),
        'estado_filtro': estado_filtro,
        'busqueda':      busqueda,
        'asesores':      User.objects.filter(is_active=True),
        'es_admin':      es_admin,
    }
    return render(request, 'prospectos/index.html', contexto)


@login_required
def crear(request):
    """Crea un prospecto desde el panel admin — vía modal AJAX del Dashboard."""
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method != 'POST':
        return redirect('prospectos:index')

    es_admin, _ = _rol(request.user)

    post_data = request.POST.copy()
    post_data['servicios_interes']    = ','.join(request.POST.getlist('servicios_interes'))
    post_data['promociones_actuales'] = ','.join(request.POST.getlist('promociones_actuales'))

    form = ProspectoForm(post_data)
    if form.is_valid():
        p = form.save(commit=False)
        # Asesor: si no es admin, el prospecto queda asignado a sí mismo automáticamente
        if not es_admin:
            p.asesor_asignado = request.user
        p.save()
        registrar(
            usuario=request.user,
            accion=f'Prospecto creado: {p.nombre}',
            modulo='prospectos',
            objeto_id=p.id,
            request=request,
        )
        if es_ajax:
            return JsonResponse({
                'ok':               True,
                'id':               p.id,
                'nombre':           p.nombre,
                'correo':           p.correo,
                'telefono':         p.telefono,
                'estado':           p.estado,
                'estado_display':   p.get_estado_display(),
                'interes_display':  p.get_interes_display(),
                'tipo_registro':    p.tipo_registro,
                'asesor': (
                    p.asesor_asignado.get_full_name() or p.asesor_asignado.username
                    if p.asesor_asignado else ''
                ),
                'fecha': timezone.localtime(p.fecha).strftime('%d/%m/%Y'),
            })
        messages.success(request, f'Prospecto "{p.nombre}" creado correctamente.')
        return redirect('prospectos:index')

    errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
    if es_ajax:
        return JsonResponse({'ok': False, 'error': errores}, status=400)
    messages.error(request, f'Error al guardar: {errores}')
    return redirect('prospectos:index')


@login_required
def editar(request, prospecto_id):
    """Edita un prospecto existente — AJAX o POST clásico."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    es_admin, _ = _rol(request.user)
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['servicios_interes']    = ','.join(request.POST.getlist('servicios_interes'))
        post_data['promociones_actuales'] = ','.join(request.POST.getlist('promociones_actuales'))

        form = ProspectoForm(post_data, request.FILES, instance=prospecto)
        if form.is_valid():
            p = form.save(commit=False)
            # Un Asesor no puede reasignar el prospecto a otro asesor desde
            # este formulario; solo Admin tiene permitido cambiar la
            # asignación. Se conserva el valor original si no es admin.
            if not es_admin:
                p.asesor_asignado = prospecto.asesor_asignado
            p.save()
            registrar(
                usuario=request.user,
                accion=f'Prospecto #{prospecto_id} ({p.nombre}) actualizado',
                modulo='prospectos',
                objeto_id=prospecto_id,
                request=request,
            )
            if es_ajax:
                return JsonResponse({
                    'ok':                   True,
                    'id':                   p.id,
                    'nombre':               p.nombre,
                    'correo':               p.correo,
                    'telefono':             p.telefono,
                    'es_referido':          p.es_referido,
                    'estado':               p.estado,
                    'estado_display':       p.get_estado_display(),
                    'interes_display':      p.get_interes_display(),
                    'tipo_registro':        p.tipo_registro,
                    'servicios_interes':    p.servicios_interes,
                    'promociones_actuales': p.promociones_actuales,
                    'notas':               p.notas or '',
                })
            messages.success(request, f'Prospecto "{p.nombre}" actualizado.')
        else:
            errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
            if es_ajax:
                return JsonResponse({'ok': False, 'error': errores}, status=400)
            messages.error(request, f'Error: {errores}')

    return redirect('prospectos:index')


@login_required
def eliminar(request, prospecto_id):
    """Elimina un prospecto — AJAX (desde tarjeta o expediente) o POST clásico."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        nombre = prospecto.nombre
        prospecto.delete()
        registrar(
            usuario=request.user,
            accion=f'Prospecto "{nombre}" eliminado',
            modulo='prospectos',
            objeto_id=prospecto_id,
            request=request,
        )
        if es_ajax:
            return JsonResponse({'ok': True, 'id': prospecto_id, 'nombre': nombre})
        messages.success(request, f'Prospecto "{nombre}" eliminado.')
        return redirect('prospectos:index')

    if es_ajax:
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    return redirect('prospectos:index')

@login_required
def expediente(request, prospecto_id):
    """Vista standalone del expediente — con protección de rol."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    es_admin, _ = _rol(request.user)

    return render(request, 'prospectos/expediente.html', {
        'prospecto':    prospecto,
        'seguimientos': prospecto.seguimientos.select_related('asesor').all(),
        'form_seg':     SeguimientoForm(),
        'asesores':     User.objects.filter(is_active=True),
        'es_admin':     es_admin,
    })


@login_required
def expediente_ajax(request, prospecto_id):
    """Devuelve JSON con los datos del expediente para el dashboard."""
    p = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, p)
    if not permitido:
        return err

    segs = list(
        p.seguimientos.select_related('asesor')
         .values('id', 'comentario', 'fecha',
                 'asesor__first_name', 'asesor__last_name', 'asesor__username')
         .order_by('-fecha')
    )
    seguimientos_data = []
    for s in segs:
        nombre_asesor = (
            f"{s['asesor__first_name']} {s['asesor__last_name']}".strip()
            or s['asesor__username']
            or 'Sistema'
        )
        seguimientos_data.append({
            'comentario':    s['comentario'],
            'fecha':         timezone.localtime(s['fecha']).strftime('%d/%m/%Y %H:%M'),
            'asesor_nombre': nombre_asesor,
        })

    _labels = {
        'seguro_vida': 'Seguro de Vida', 'medico':    'Gastos Médicos',
        'auto':        'Seguro de Auto', 'hogar':     'Seguro de Hogar',
        'inversion':   'Inversión y Ahorro', 'empresarial': 'Empresarial',
    }

    def _csv_to_labels(csv_str):
        if not csv_str:
            return []
        return [_labels.get(v.strip(), v.strip()) for v in csv_str.split(',') if v.strip()]

    return JsonResponse({
        'ok':                        True,
        'id':                        p.id,
        'nombre':                    p.nombre,
        'correo':                    p.correo,
        'telefono':                  p.telefono,
        'es_referido':               p.es_referido,
        'nombre_referente':          p.nombre_referente or '',
        'interes':                   p.interes,
        'interes_display':           p.get_interes_display(),
        'estado':                    p.estado,
        'estado_display':            p.get_estado_display(),
        'asesor': (
            p.asesor_asignado.get_full_name() or p.asesor_asignado.username
            if p.asesor_asignado else ''
        ),
        'fecha_alta':                p.fecha.strftime('%d/%m/%Y'),
        'fecha_contacto':            timezone.localtime(p.fecha_contacto).strftime('%d/%m/%Y %H:%M') if p.fecha_contacto else '',
        'notas':                     p.notas or '',
        'mensaje':                   p.mensaje or '',
        'tipo_registro':             p.tipo_registro,
        'tipo_registro_display':     p.get_tipo_registro_display(),
        'servicios_interes':         p.servicios_interes,
        'servicios_interes_lista':   _csv_to_labels(p.servicios_interes),
        'promociones_actuales':      p.promociones_actuales,
        'promociones_actuales_lista': _csv_to_labels(p.promociones_actuales),
        'seguimientos':              seguimientos_data,
        'url_editar':                f'/prospectos/{p.id}/editar/',
        'url_convertir':             f'/prospectos/{p.id}/convertir/',
        'url_eliminar':              f'/prospectos/{p.id}/eliminar/',
        'url_seguimiento':           f'/prospectos/{p.id}/seguimiento/',
    })


@login_required
def agregar_seguimiento(request, prospecto_id):
    """Agrega un seguimiento — solo si el asesor tiene acceso al prospecto."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    if request.method == 'POST':
        form = SeguimientoForm(request.POST)
        if form.is_valid():
            seg = form.save(commit=False)
            seg.prospecto = prospecto
            seg.asesor    = request.user
            seg.save()
            registrar(
                usuario=request.user,
                accion=f'Seguimiento agregado al prospecto #{prospecto_id} ({prospecto.nombre})',
                modulo='prospectos',
                objeto_id=prospecto_id,
                request=request,
            )
            messages.success(request, 'Comentario de seguimiento registrado.')
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
    return redirect('prospectos:expediente', prospecto_id=prospecto_id)


@login_required
def convertir(request, prospecto_id):
    """Convierte un prospecto a cliente — AJAX o POST clásico."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        prospecto.estado        = 'convertido'
        prospecto.tipo_registro = 'cliente'
        prospecto.save(update_fields=['estado', 'tipo_registro'])
        registrar(
            usuario=request.user,
            accion=f'Prospecto #{prospecto_id} ({prospecto.nombre}) convertido a cliente',
            modulo='prospectos',
            objeto_id=prospecto_id,
            request=request,
        )
        if es_ajax:
            return JsonResponse({
                'ok':                    True,
                'id':                    prospecto.id,
                'nombre':                prospecto.nombre,
                'estado':                prospecto.estado,
                'estado_display':        prospecto.get_estado_display(),
                'tipo_registro':         prospecto.tipo_registro,
                'tipo_registro_display': prospecto.get_tipo_registro_display(),
            })
        messages.success(request, f'"{prospecto.nombre}" marcado como cliente convertido.')
    return redirect('prospectos:expediente', prospecto_id=prospecto_id)


@login_required
def cambiar_estado_ajax(request, prospecto_id):
    """Cambia solo el estado del prospecto — usado por el modal Ver/Cambiar estado."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    nuevo_estado = request.POST.get('estado')
    estados_validos = [e[0] for e in Prospecto.ESTADO_CHOICES]
    if nuevo_estado not in estados_validos:
        return JsonResponse({'ok': False, 'error': 'Estado no válido'}, status=400)

    estado_anterior = prospecto.estado
    prospecto.estado = nuevo_estado
    if nuevo_estado == 'convertido':
        prospecto.tipo_registro = 'cliente'
    prospecto.save()

    registrar(
        usuario=request.user,
        accion=f'Prospecto #{prospecto_id} ({prospecto.nombre}) cambió de "{estado_anterior}" a "{nuevo_estado}"',
        modulo='prospectos',
        objeto_id=prospecto_id,
        request=request,
    )
    return JsonResponse({
        'ok':                    True,
        'id':                    prospecto.id,
        'estado':                prospecto.estado,
        'estado_display':        prospecto.get_estado_display(),
        'tipo_registro':         prospecto.tipo_registro,
        'tipo_registro_display': prospecto.get_tipo_registro_display(),
    })


@login_required
def mensaje_generado_ajax(request, prospecto_id, clave):
    """
    Devuelve el texto ya personalizado de una plantilla de mensaje para este
    prospecto. Todavía NO envía nada por WhatsApp ni correo — solo genera el
    texto, listo para que una fase posterior lo conecte a wa.me o SMTP.
    """
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)

    permitido, err = _verificar_acceso_prospecto(request, prospecto)
    if not permitido:
        return err

    texto = mensajes.generar_mensaje(clave, prospecto)
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Plantilla no encontrada'}, status=404)

    return JsonResponse({'ok': True, 'clave': clave, 'texto': texto})