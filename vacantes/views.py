import os
from datetime import date
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Vacante
from .forms  import VacanteForm
from historial.models import registrar
from usuarios.permisos import solo_admin


# ── Vista pública: lista de vacantes activas y NO vencidas ────────────────────
def index(request):
    Vacante.sincronizar_vencidas()
    vacantes_general        = Vacante.objects.filter(estado='activa').order_by('-creada')
    vacantes_estudiantes    = vacantes_general.filter(publico_objetivo='estudiantes')
    vacantes_jubilados      = vacantes_general.filter(publico_objetivo='jubilados')
    vacantes_amas_casa      = vacantes_general.filter(publico_objetivo='amas_casa')
    vacantes_profesionistas = vacantes_general.filter(publico_objetivo='profesionistas')

    # Abre por defecto la primera categoría que sí tenga vacantes activas
    tab_inicial = 'general'
    for clave, qs in (
        ('estudiantes', vacantes_estudiantes),
        ('jubilados', vacantes_jubilados),
        ('amas', vacantes_amas_casa),
        ('profesionistas', vacantes_profesionistas),
    ):
        if qs.exists():
            tab_inicial = clave
            break

    context = {
        'vacantes':                vacantes_general,
        'vacantes_form':            Vacante.objects.filter(estado='activa').order_by('titulo'),
        'vacantes_general':         vacantes_general,
        'vacantes_estudiantes':     vacantes_estudiantes,
        'vacantes_jubilados':       vacantes_jubilados,
        'vacantes_amas_casa':       vacantes_amas_casa,
        'vacantes_profesionistas':  vacantes_profesionistas,
        'tab_inicial':              tab_inicial,
        'hay_vacantes':             vacantes_general.exists(),
    }
    return render(request, 'vacantes/index.html', context)
# ── Admin: lista todas las vacantes con filtros y KPIs ───────────────────────
@login_required
@solo_admin
def lista(request):
    Vacante.sincronizar_vencidas()

    qs       = Vacante.objects.all()
    estado   = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')
    publico  = request.GET.get('publico_objetivo', '')

    if estado:
        qs = qs.filter(estado=estado)
    if publico:
        qs = qs.filter(publico_objetivo=publico)
    if busqueda:
        qs = qs.filter(titulo__icontains=busqueda) | qs.filter(area__icontains=busqueda)

    contexto = {
        'vacantes':         qs,
        'total':            Vacante.objects.count(),
        'activas':          Vacante.objects.filter(estado='activa').count(),
        'pausadas':         Vacante.objects.filter(estado='pausada').count(),
        'cerradas':         Vacante.objects.filter(estado='cerrada').count(),
        'vencidas':         Vacante.objects.filter(estado='vencida').count(),
        'estado_filtro':    estado,
        'publico_filtro':   publico,
        'busqueda':         busqueda,
    }
    return render(request, 'vacantes/lista.html', contexto)


# ── Admin: crear vacante ──────────────────────────────────────────────────────
@login_required
@solo_admin
def crear(request):
    if request.method == 'POST':
        form = VacanteForm(request.POST, request.FILES)
        if form.is_valid():
            v = form.save()
            registrar(
                usuario=request.user,
                accion=f'Vacante creada: "{v.titulo}" ({v.area})',
                modulo='vacantes',
                objeto_id=v.id,
                request=request,
            )
            messages.success(request, f'Vacante "{v.titulo}" creada correctamente.')
        else:
            errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
            messages.error(request, f'Error al guardar: {errores}')
    return redirect('vacantes:lista')


# ── Admin: datos JSON para modal editar (GET) y guardar cambios (POST) ────────
@login_required
@solo_admin
def editar(request, vacante_id):
    vacante = get_object_or_404(Vacante, id=vacante_id)

    if request.method == 'GET':
        return JsonResponse({
            'id':          vacante.id,
            'titulo':      vacante.titulo,
            'area':        vacante.area,
            'descripcion': vacante.descripcion,
            'requisitos':  vacante.requisitos  or '',
            'ubicacion':   vacante.ubicacion   or '',
            'modalidad':   vacante.modalidad,
            'sueldo':      vacante.sueldo      or '',
            'estado':      vacante.estado,
            'publico_objetivo': vacante.publico_objetivo,
            'fecha_limite': str(vacante.fecha_limite) if vacante.fecha_limite else '',
            'pdf_url':     vacante.pdf_convocatoria.url if vacante.pdf_convocatoria else '',
            'img_url':     vacante.imagen.url           if vacante.imagen           else '',
        })

    # POST: guardar cambios
    if request.POST.get('borrar_pdf') and vacante.pdf_convocatoria:
        try:
            os.remove(vacante.pdf_convocatoria.path)
        except Exception:
            pass
        vacante.pdf_convocatoria = None
        vacante.save(update_fields=['pdf_convocatoria'])
        vacante.refresh_from_db()

    form = VacanteForm(request.POST, request.FILES, instance=vacante)
    if form.is_valid():
        v = form.save()
        registrar(
            usuario=request.user,
            accion=f'Vacante #{vacante_id} "{v.titulo}" actualizada',
            modulo='vacantes',
            objeto_id=vacante_id,
            request=request,
        )
        messages.success(request, f'Vacante "{v.titulo}" actualizada.')
    else:
        errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
        messages.error(request, f'Error: {errores}')
    return redirect('vacantes:lista')


# ── Admin: cambiar estado por AJAX ────────────────────────────────────────────
@login_required
@solo_admin
def toggle_estado(request, vacante_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    v = get_object_or_404(Vacante, id=vacante_id)
    estado_anterior = v.estado
    ciclo = {'activa': 'pausada', 'pausada': 'cerrada', 'cerrada': 'activa'}
    v.estado = ciclo.get(v.estado, 'activa')
    v.save()

    registrar(
        usuario=request.user,
        accion=f'Vacante #{vacante_id} "{v.titulo}" cambió de "{estado_anterior}" a "{v.estado}"',
        modulo='vacantes',
        objeto_id=vacante_id,
        request=request,
    )

    return JsonResponse({
        'ok':     True,
        'estado': v.estado,
        'label':  v.get_estado_display(),
        'activa': v.activa,
    })


# ── Admin: eliminar vacante ───────────────────────────────────────────────────
@login_required
@solo_admin
def eliminar(request, vacante_id):
    v = get_object_or_404(Vacante, id=vacante_id)
    if request.method == 'POST':
        titulo = v.titulo
        for campo in (v.pdf_convocatoria, v.imagen):
            if campo:
                try:
                    os.remove(campo.path)
                except Exception:
                    pass
        v.delete()
        registrar(
            usuario=request.user,
            accion=f'Vacante "{titulo}" eliminada',
            modulo='vacantes',
            objeto_id=vacante_id,
            request=request,
        )
        messages.success(request, f'Vacante "{titulo}" eliminada.')
    return redirect('vacantes:lista')
