from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Prospecto, SeguimientoProspecto
from .forms  import ProspectoForm, ProspectoPublicoForm, SeguimientoForm
from historial.models import registrar


def nuevo(request):
    """Vista pública: formulario de contacto del sitio."""
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


@login_required
def index(request):
    """Vista del panel admin: lista de prospectos."""
    qs = Prospecto.objects.all()
    estado_filtro = request.GET.get('estado', '')
    busqueda      = request.GET.get('q', '')
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)
    if busqueda:
        qs = qs.filter(nombre__icontains=busqueda) | qs.filter(correo__icontains=busqueda)
    contexto = {
        'prospectos':    qs,
        'total':         Prospecto.objects.count(),
        'nuevos':        Prospecto.objects.filter(estado='nuevo').count(),
        'contactados':   Prospecto.objects.filter(estado='contactado').count(),
        'convertidos':   Prospecto.objects.filter(estado='convertido').count(),
        'estado_filtro': estado_filtro,
        'busqueda':      busqueda,
        'asesores':      User.objects.filter(is_active=True),
    }
    return render(request, 'prospectos/index.html', contexto)


@login_required
def crear(request):
    """Crea un prospecto desde el panel admin (modal)."""
    if request.method == 'POST':
        form = ProspectoForm(request.POST)
        if form.is_valid():
            p = form.save()
            registrar(
                usuario=request.user,
                accion=f'Prospecto creado: {p.nombre}',
                modulo='prospectos',
                objeto_id=p.id,
                request=request,
            )
            messages.success(request, f'Prospecto "{p.nombre}" creado correctamente.')
        else:
            errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
            messages.error(request, f'Error al guardar: {errores}')
    return redirect('prospectos:index')


@login_required
@login_required
def editar(request, prospecto_id):
    """Edita un prospecto existente."""
    from django.http import JsonResponse
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    prospecto = get_object_or_404(Prospecto, id=prospecto_id)
    if request.method == 'POST':
        # servicios_interes y promociones_actuales llegan como lista
        # (múltiples valores del mismo name); los unimos en CSV antes del form
        post_data = request.POST.copy()
        si_vals = request.POST.getlist('servicios_interes')
        pr_vals = request.POST.getlist('promociones_actuales')
        post_data['servicios_interes']    = ','.join(si_vals)
        post_data['promociones_actuales'] = ','.join(pr_vals)

        form = ProspectoForm(post_data, request.FILES, instance=prospecto)
        if form.is_valid():
            p = form.save()
            registrar(
                usuario=request.user,
                accion=f'Prospecto #{prospecto_id} ({p.nombre}) actualizado',
                modulo='prospectos',
                objeto_id=prospecto_id,
                request=request,
            )
            if es_ajax:
                return JsonResponse({
                    'ok':                  True,
                    'id':                  p.id,
                    'nombre':              p.nombre,
                    'correo':              p.correo,
                    'telefono':            p.telefono,
                    'es_referido':         p.es_referido,
                    'estado':              p.estado,
                    'estado_display':      p.get_estado_display(),
                    'interes_display':     p.get_interes_display(),
                    'tipo_registro':       p.tipo_registro,
                    'servicios_interes':   p.servicios_interes,
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
    """Elimina un prospecto."""
    p = get_object_or_404(Prospecto, id=prospecto_id)
    if request.method == 'POST':
        nombre = p.nombre
        p.delete()
        registrar(
            usuario=request.user,
            accion=f'Prospecto "{nombre}" eliminado',
            modulo='prospectos',
            objeto_id=prospecto_id,
            request=request,
        )
        messages.success(request, f'Prospecto "{nombre}" eliminado.')
    return redirect('prospectos:index')

@login_required
def expediente(request, prospecto_id):
    """Vista de expediente completo del prospecto — standalone."""
    prospecto    = get_object_or_404(Prospecto, id=prospecto_id)
    seguimientos = prospecto.seguimientos.select_related('asesor').all()
    form_seg     = SeguimientoForm()
    asesores     = User.objects.filter(is_active=True)

    return render(request, 'prospectos/expediente.html', {
        'prospecto':    prospecto,
        'seguimientos': seguimientos,
        'form_seg':     form_seg,
        'asesores':     asesores,
    })


@login_required
def expediente_ajax(request, prospecto_id):
    """Devuelve JSON con todos los datos del expediente para el dashboard."""
    from django.http import JsonResponse
    p  = get_object_or_404(Prospecto, id=prospecto_id)
    segs = list(
        p.seguimientos.select_related('asesor')
         .values('id', 'comentario', 'fecha', 'asesor__first_name',
                 'asesor__last_name', 'asesor__username')
         .order_by('-fecha')
    )
    # Serializar seguimientos
    seguimientos_data = []
    for s in segs:
        nombre_asesor = (
            f"{s['asesor__first_name']} {s['asesor__last_name']}".strip()
            or s['asesor__username']
            or 'Sistema'
        )
        seguimientos_data.append({
            'comentario':    s['comentario'],
            'fecha':         s['fecha'].strftime('%d/%m/%Y %H:%M'),
            'asesor_nombre': nombre_asesor,
        })

    # Etiquetas legibles para los valores CSV
    _labels = {
        'seguro_vida': 'Seguro de Vida', 'medico': 'Gastos Médicos',
        'auto': 'Seguro de Auto', 'hogar': 'Seguro de Hogar',
        'inversion': 'Inversión y Ahorro', 'empresarial': 'Empresarial',
    }
    def _csv_to_labels(csv_str):
        if not csv_str:
            return []
        return [_labels.get(v.strip(), v.strip()) for v in csv_str.split(',') if v.strip()]

    return JsonResponse({
        'ok':  True,
        'id':  p.id,
        'nombre':          p.nombre,
        'correo':          p.correo,
        'telefono':        p.telefono,
        'es_referido':     p.es_referido,
        'nombre_referente': p.nombre_referente or '',
        'interes_display': p.get_interes_display(),
        'estado':          p.estado,
        'estado_display':  p.get_estado_display(),
        'asesor':          (
            p.asesor_asignado.get_full_name() or p.asesor_asignado.username
            if p.asesor_asignado else ''
        ),
        'fecha_alta':      p.fecha.strftime('%d/%m/%Y'),
        'fecha_contacto':  p.fecha_contacto.strftime('%d/%m/%Y %H:%M') if p.fecha_contacto else '',
        'notas':           p.notas or '',
        'mensaje':         p.mensaje or '',
        'tipo_registro':          p.tipo_registro,
        'tipo_registro_display':  p.get_tipo_registro_display(),
        'servicios_interes':      p.servicios_interes,
        'servicios_interes_lista': _csv_to_labels(p.servicios_interes),
        'promociones_actuales':      p.promociones_actuales,
        'promociones_actuales_lista': _csv_to_labels(p.promociones_actuales),
        'seguimientos':    seguimientos_data,
        'url_editar':      f'/prospectos/{p.id}/editar/',
        'url_convertir':   f'/prospectos/{p.id}/convertir/',
        'url_eliminar':    f'/prospectos/{p.id}/eliminar/',
        'url_seguimiento': f'/prospectos/{p.id}/seguimiento/',
    })

@login_required
def agregar_seguimiento(request, prospecto_id):
    """Agrega un comentario de seguimiento vía POST."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)
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
    """Convierte un prospecto a cliente (cambia estado a 'convertido')."""
    from django.http import JsonResponse
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    prospecto = get_object_or_404(Prospecto, id=prospecto_id)
    if request.method == 'POST':
        prospecto.estado = 'convertido'
        prospecto.save(update_fields=['estado'])
        registrar(
            usuario=request.user,
            accion=f'Prospecto #{prospecto_id} ({prospecto.nombre}) convertido a cliente',
            modulo='prospectos',
            objeto_id=prospecto_id,
            request=request,
        )
        if es_ajax:
            return JsonResponse({
                'ok':     True,
                'id':     prospecto.id,
                'nombre': prospecto.nombre,
                'estado': prospecto.estado,
                'estado_display': prospecto.get_estado_display(),
            })
        messages.success(request, f'"{prospecto.nombre}" marcado como cliente convertido.')
    return redirect('prospectos:expediente', prospecto_id=prospecto_id)