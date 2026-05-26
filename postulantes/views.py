from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

from .models import Postulante
from vacantes.models import Vacante
from historial.models import registrar


# ── Vista pública: formulario de postulación ─────────────────────────────────
def crear(request):
    if request.method == 'POST':
        # Validar que se subió un CV
        cv = request.FILES.get('cv')
        if not cv:
            vacantes = Vacante.objects.filter(activa=True)
            return render(request, 'postulantes/formulario.html', {
                'vacantes': vacantes,
                'error': 'Por favor adjunta tu CV en formato PDF.',
                'post': request.POST,
            })
        # Validar tipo de archivo
        nombre_cv = cv.name.lower()
        if not nombre_cv.endswith('.pdf') and cv.content_type not in ('application/pdf',):
            vacantes = Vacante.objects.filter(activa=True)
            return render(request, 'postulantes/formulario.html', {
                'vacantes': vacantes,
                'error': 'Solo se aceptan archivos PDF para el CV.',
                'post': request.POST,
            })

        # Validar tamaño (5 MB)
        if cv.size > 5 * 1024 * 1024:
            vacantes = Vacante.objects.filter(activa=True)
            return render(request, 'postulantes/formulario.html', {
                'vacantes': vacantes,
                'error': 'El CV no puede superar 5 MB.',
                'post': request.POST,
            })

        vacante_id = request.POST.get('vacante')
        vacante = None
        if vacante_id:
            try:
                vacante = Vacante.objects.get(pk=int(vacante_id))
            except (Vacante.DoesNotExist, ValueError):
                pass

        postulante = Postulante.objects.create(
            nombre   = request.POST.get('nombre', '').strip(),
            correo   = request.POST.get('correo', '').strip(),
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

    vacantes = Vacante.objects.filter(activa=True)
    return render(request, 'postulantes/formulario.html', {'vacantes': vacantes})


def exito(request):
    return render(request, 'postulantes/exito.html')


# ── Vista admin: lista todos los postulantes ─────────────────────────────────
@login_required
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
            Q(correo__icontains=busqueda)
    )
    paginator = Paginator(qs, 10)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    contexto = {
        'postulantes':    page_obj,          # ahora es un Page object
        'page_obj':       page_obj,
        'vacantes_todas': Vacante.objects.all().order_by('titulo'),
        'total':          Postulante.objects.count(),
        # KPIs con los 6 estados
        'nuevos':         Postulante.objects.filter(estado='nuevo').count(),
        'en_revision':    Postulante.objects.filter(estado='revision').count(),
        'en_entrevista':  Postulante.objects.filter(estado='entrevista').count(),
        'finalistas':     Postulante.objects.filter(estado='finalista').count(),
        'contratados':    Postulante.objects.filter(estado='aceptado').count(),
        'rechazados':     Postulante.objects.filter(estado='rechazado').count(),
        'estado_filtro':  estado,
        'vacante_filtro': vacante_id,
        'busqueda':       busqueda,
        'estados_choices': Postulante.ESTADO_CHOICES,
    }
    return render(request, 'postulantes/lista.html', contexto)

# ── AJAX: cambiar estado ─────────────────────────────────────────────────────
@login_required
def cambiar_estado_ajax(request, post_id):
    if request.method == 'POST':
        postulante = get_object_or_404(Postulante, id=post_id)
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Postulante.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            estado_anterior = postulante.estado
            postulante.estado = nuevo_estado
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
            })
        return JsonResponse({'ok': False, 'error': 'Estado no válido'}, status=400)
    return JsonResponse({'ok': False}, status=405)


# ── Vista admin: eliminar ─────────────────────────────────────────────────────
@login_required
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
