from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Postulante
from vacantes.models import Vacante
from historial.models import registrar
from usuarios.permisos import solo_admin
from . import mensajes
import json

# ── Vista admin: cambiar estado (legacy, ver también cambiar_estado_ajax) ──
# HALLAZGO FASE D (punto 10): esta vista estaba expuesta sin @login_required
# ni @solo_admin, permitiendo a cualquier visitante no autenticado cambiar
# el estado de un Postulante vía POST. Se protege con el mismo criterio ya
# usado en el resto del módulo (ver cambiar_estado_ajax más abajo).
@login_required
@solo_admin
def cambiar_estado(request, id):
    if request.method == 'POST':

        data = json.loads(request.body)

        postulante = get_object_or_404(Postulante, id=id)

        postulante.estado = data['estado']

        postulante.save()

        return JsonResponse({
            'success': True
        })
# ── Vista pública: formulario de postulación ─────────────────────────────────
def crear(request):
    if request.method == 'POST':
        # Si algo falla, regresamos al usuario a la misma página de donde vino
        # (hoy siempre /vacantes/), en vez de mandarlo a una plantilla distinta.
        origen = request.META.get('HTTP_REFERER') or '/vacantes/'

        # Validar que se subió un CV
        cv = request.FILES.get('cv')
        if not cv:
            messages.error(request, 'Por favor adjunta tu CV en formato PDF.')
            return redirect(origen)

        # Validar tipo de archivo
        nombre_cv = cv.name.lower()
        if not nombre_cv.endswith('.pdf') and cv.content_type not in ('application/pdf',):
            messages.error(request, 'Solo se aceptan archivos PDF para el CV.')
            return redirect(origen)

        # Validar tamaño (5 MB)
        if cv.size > 5 * 1024 * 1024:
            messages.error(request, 'El CV no puede superar 5 MB.')
            return redirect(origen)

        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip()
        if not nombre or not correo:
            messages.error(request, 'Nombre y correo son obligatorios.')
            return redirect(origen)

        vacante_id = request.POST.get('vacante')
        vacante = None
        if vacante_id:
            try:
                vacante = Vacante.objects.get(pk=int(vacante_id))
            except (Vacante.DoesNotExist, ValueError):
                pass

        postulante = Postulante.objects.create(
            nombre   = nombre,
            correo   = correo,
            telefono = request.POST.get('telefono', '').strip(),
            linkedin = request.POST.get('linkedin', '').strip() or None,
            cv       = cv,
            vacante  = vacante,
        )

        # Registrar en historial
        vacante_txt = vacante.titulo if vacante else 'sin vacante específica'
        registrar(
            usuario=None,
            accion=f'Nueva postulación de {postulante.nombre} para "{vacante_txt}"',
            modulo='postulantes',
            objeto_id=postulante.id,
            request=request,
        )

        # Redirigir según origen
        next_url = request.POST.get('next', '')
        referer  = request.META.get('HTTP_REFERER', '')
        if 'dashboard' in referer or 'dashboard' in next_url:
            messages.success(request, '¡Postulación registrada correctamente!')
            return redirect('/dashboard/#postulantes')
        return redirect('postulantes:exito')

    vacantes = Vacante.objects.filter(estado='activa')
    return render(request, 'postulantes/formulario.html', {'vacantes': vacantes})


def exito(request):
    return render(request, 'postulantes/exito.html')


# ── Vista admin: lista todos los postulantes ─────────────────────────────────
@login_required
@solo_admin
def lista(request):
    from django.core.paginator import Paginator

    qs = Postulante.objects.select_related('vacante').order_by('-fecha')

    estado     = request.GET.get('estado', '')
    vacante_id = request.GET.get('vacante', '')
    busqueda   = request.GET.get('q', '')

    if estado:
        qs = qs.filter(estado=estado)

    if vacante_id:
        qs = qs.filter(vacante_id=vacante_id)

    if busqueda:
        qs = qs.filter(
            Q(nombre__icontains=busqueda) |
            Q(correo__icontains=busqueda) |
            Q(telefono__icontains=busqueda)
        )

    paginator = Paginator(qs, 10)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    contexto = {
        'postulantes': page_obj,
        'page_obj': page_obj,

        'vacantes_todas': Vacante.objects.all().order_by('titulo'),

        'total': Postulante.objects.count(),

        # KPIs
        'nuevos': Postulante.objects.filter(estado='nuevo').count(),
        'en_revision': Postulante.objects.filter(estado='revisado').count(),
        'en_entrevista': Postulante.objects.filter(estado='entrevista').count(),
        'finalistas': Postulante.objects.filter(estado='finalista').count(),
        'contratados': Postulante.objects.filter(estado='contratado').count(),
        'rechazados': Postulante.objects.filter(estado='rechazado').count(),

        'estado_filtro': estado,
        'vacante_filtro': vacante_id,
        'busqueda': busqueda,

        'estados_choices': Postulante.ESTADO_CHOICES,
    }

    return render(request, 'postulantes/lista.html', contexto)

# ── AJAX: cambiar estado ─────────────────────────────────────────────────────
@login_required
@solo_admin
def cambiar_estado_ajax(request, post_id):
    if request.method == 'POST':
        postulante = get_object_or_404(Postulante, id=post_id)
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Postulante.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            estado_anterior = postulante.estado
            postulante.estado = nuevo_estado

            # La fecha de entrevista solo se captura/actualiza cuando el
            # nuevo estado es 'entrevista'. Si se manda vacía o el estado
            # es otro, no se toca fecha_entrevista (se conserva lo que
            # ya hubiera, por si luego regresan el estado a "Entrevista").
            fecha_entrevista_raw = request.POST.get('fecha_entrevista', '').strip()
            if nuevo_estado == 'entrevista' and fecha_entrevista_raw:
                fecha_entrevista = parse_datetime(fecha_entrevista_raw)
                if fecha_entrevista and timezone.is_naive(fecha_entrevista):
                    fecha_entrevista = timezone.make_aware(fecha_entrevista)
                if fecha_entrevista:
                    postulante.fecha_entrevista = fecha_entrevista

            postulante.save()
            postulante.refresh_from_db()
            registrar(
                usuario=request.user,
                accion=f'{postulante.nombre} cambió de "{dict(Postulante.ESTADO_CHOICES).get(estado_anterior)}" a "{postulante.get_estado_display()}"',  
                modulo='postulantes',
                objeto_id=post_id,
                request=request,
            )
            return JsonResponse({
                'ok': True,
                'estado': postulante.estado,
                'estado_display': postulante.get_estado_display(),
                'fecha_entrevista': (
                    timezone.localtime(postulante.fecha_entrevista).strftime('%Y-%m-%dT%H:%M')
                    if postulante.fecha_entrevista else None
                ),
            })
        return JsonResponse({'ok': False, 'error': 'Estado no válido'}, status=400)
    return JsonResponse({'ok': False}, status=405)


# ── Vista admin: eliminar ─────────────────────────────────────────────────────
@login_required
@solo_admin
def eliminar(request, post_id):
    postulante = get_object_or_404(Postulante, id=post_id)
    if request.method == 'POST':
        nombre = postulante.nombre
        postulante.delete()
        registrar(
            usuario=request.user,
            accion=f'Postulante "{nombre}" eliminado',
            modulo='postulantes',
            objeto_id=post_id,
            request=request,
        )
        messages.success(request, f'Postulante "{nombre}" eliminado.')
    return redirect('postulantes:lista')

# ── AJAX: eliminar (sin redirect, retorna JSON) ───────────────────────────────
@login_required
@solo_admin
def eliminar_ajax(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    postulante = get_object_or_404(Postulante, id=post_id)
    nombre = postulante.nombre
    estado_eliminado = postulante.estado
    postulante.delete()
    registrar(
        usuario=request.user,
        accion=f'Postulante "{nombre}" eliminado del sistema',
        modulo='postulantes',
        objeto_id=post_id,
        request=request,
    )
    # Contadores actualizados para el frontend
    from django.db.models import Count as DCount
    contadores = {
        'total':      Postulante.objects.count(),
        'nuevo':      Postulante.objects.filter(estado='nuevo').count(),
        'revisado':   Postulante.objects.filter(estado='revisado').count(),
        'entrevista': Postulante.objects.filter(estado='entrevista').count(),
        'finalista':  Postulante.objects.filter(estado='finalista').count(),
        'contratado': Postulante.objects.filter(estado='contratado').count(),
        'rechazado':  Postulante.objects.filter(estado='rechazado').count(),
    }
    return JsonResponse({
        'ok': True,
        'nombre': nombre,
        'contadores': contadores,
    })

# ── AJAX: detalle postulante ──────────────────────────────────────────────────
@login_required
@solo_admin
def detalle_ajax(request, post_id):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    p = get_object_or_404(
        Postulante.objects.select_related('vacante'),
        id=post_id
    )
    return JsonResponse({
        'ok': True,
        'id':       p.id,
        'nombre':   p.nombre,
        'correo':   p.correo,
        'telefono': p.telefono or '—',
        'linkedin': p.linkedin or '',
        'cv_url':   p.cv.url if p.cv else '',
        'vacante':  p.vacante.titulo if p.vacante else '—',
        'fecha':    p.fecha.strftime('%d/%m/%Y %H:%M'),
        'estado':   p.estado,
        'estado_display': p.get_estado_display(),
        'notas':    p.notas or '',
        'fecha_entrevista': (
            timezone.localtime(p.fecha_entrevista).strftime('%d/%m/%Y %H:%M')
            if p.fecha_entrevista else ''
        ),
        'fecha_entrevista_iso': (
            timezone.localtime(p.fecha_entrevista).strftime('%Y-%m-%dT%H:%M')
            if p.fecha_entrevista else ''
        ),
    })
# ── AJAX: crear postulante desde el dashboard ─────────────────────────────────
@login_required
@solo_admin
def crear_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    nombre   = request.POST.get('nombre', '').strip()
    correo   = request.POST.get('correo', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    linkedin = request.POST.get('linkedin', '').strip() or None
    vacante_id = request.POST.get('vacante_id', '').strip()

    # Validaciones mínimas
    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)
    if not correo or '@' not in correo:
        return JsonResponse({'ok': False, 'error': 'Ingresa un correo válido.'}, status=400)

    # Vacante (opcional)
    vacante = None
    if vacante_id:
        try:
            vacante = Vacante.objects.get(pk=int(vacante_id))
        except (Vacante.DoesNotExist, ValueError):
            pass

    # CV (opcional desde el dashboard)
    cv_file = request.FILES.get('cv')
    if cv_file:
        if not cv_file.name.lower().endswith('.pdf') and cv_file.content_type != 'application/pdf':
            return JsonResponse({'ok': False, 'error': 'El CV debe ser un archivo PDF.'}, status=400)
        if cv_file.size > 5 * 1024 * 1024:
            return JsonResponse({'ok': False, 'error': 'El CV no puede superar 5 MB.'}, status=400)

    postulante = Postulante.objects.create(
        nombre   = nombre,
        correo   = correo,
        telefono = telefono or None,
        linkedin = linkedin,
        cv       = cv_file if cv_file else '',
        vacante  = vacante,
        estado   = 'nuevo',
    )

    registrar(
        usuario=request.user,
        accion=f'Postulante "{postulante.nombre}" registrado desde el dashboard',
        modulo='postulantes',
        objeto_id=postulante.id,
        request=request,
    )

    contadores = {
        'total':      Postulante.objects.count(),
        'nuevo':      Postulante.objects.filter(estado='nuevo').count(),
        'revisado':   Postulante.objects.filter(estado='revisado').count(),
        'entrevista': Postulante.objects.filter(estado='entrevista').count(),
        'finalista':  Postulante.objects.filter(estado='finalista').count(),
        'contratado': Postulante.objects.filter(estado='contratado').count(),
        'rechazado':  Postulante.objects.filter(estado='rechazado').count(),
    }

    return JsonResponse({
        'ok':       True,
        'id':       postulante.id,
        'nombre':   postulante.nombre,
        'correo':   postulante.correo,
        'telefono': postulante.telefono or '',
        'vacante':  vacante.titulo if vacante else '—',
        'fecha':    postulante.fecha.strftime('%d/%m/%Y'),
        'estado':   postulante.estado,
        'estado_display': postulante.get_estado_display(),
        'cv_url':   postulante.cv.url if postulante.cv else '',
        'contadores': contadores,
    })

# ── AJAX: guardar nota interna ────────────────────────────────────────────────
@login_required
@solo_admin
def guardar_nota_ajax(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    postulante = get_object_or_404(Postulante, id=post_id)
    texto = request.POST.get('notas', '').strip()

    # Detectar si hubo cambio real para no ensuciar el historial
    hubo_cambio = (postulante.notas or '') != texto

    postulante.notas = texto if texto else None
    postulante.save(update_fields=['notas'])

    if hubo_cambio:
        accion = (
            f'Nota actualizada para "{postulante.nombre}"'
            if texto
            else f'Nota eliminada para "{postulante.nombre}"'
        )
        registrar(
            usuario=request.user,
            accion=accion,
            modulo='postulantes',
            objeto_id=post_id,
            request=request,
        )

    return JsonResponse({
        'ok':    True,
        'notas': postulante.notas or '',
    })


# ── API JSON: mensaje generado para un postulante (WhatsApp) ─────────────────
@login_required
@solo_admin
def mensaje_generado_ajax(request, post_id, clave):
    """
    Devuelve el texto ya personalizado de una plantilla de mensaje para este
    postulante. Solo genera el texto — el envío por WhatsApp lo hace el
    frontend con la URL wa.me.
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    postulante = get_object_or_404(Postulante, id=post_id)

    texto = mensajes.generar_mensaje(clave, postulante)
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Plantilla no encontrada'}, status=404)

    return JsonResponse({'ok': True, 'clave': clave, 'texto': texto})
