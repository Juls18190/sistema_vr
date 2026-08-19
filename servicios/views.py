from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Servicio
from .forms import ServicioForm
from historial.models import registrar
from usuarios.permisos import solo_admin


def index(request):
    servicios = Servicio.objects.filter(activo=True).order_by('orden')
    return render(request, 'servicios/index.html', {'servicios': servicios})


# ── AJAX: detalle de un servicio ──────────────────────────────────────────────
@login_required
@solo_admin
def detalle_ajax(request, serv_id):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    s = get_object_or_404(Servicio, id=serv_id)
    return JsonResponse({
        'ok': True,
        'id':                s.id,
        'nombre':            s.nombre,
        'categoria':         s.categoria,
        'categoria_display': s.get_categoria_display(),
        'descripcion_corta': s.descripcion_corta,
        'descripcion':       s.descripcion,
        'orden':             s.orden,
        'activo':            s.activo,
    })


# ── AJAX: editar un servicio ──────────────────────────────────────────────────
@login_required
@solo_admin
@require_POST
def editar_ajax(request, serv_id):
    s = get_object_or_404(Servicio, id=serv_id)
    form = ServicioForm(request.POST, request.FILES, instance=s)
    if not form.is_valid():
        errores = '; '.join(
            f'{f}: {", ".join(e)}' for f, e in form.errors.items()
        )
        return JsonResponse({'ok': False, 'error': errores}, status=400)

    servicio = form.save()

    registrar(
        usuario=request.user,
        accion=f'Servicio editado: "{servicio.nombre}" ({servicio.get_categoria_display()})',
        modulo='servicios',
        objeto_id=servicio.id,
        request=request,
    )

    return JsonResponse({
        'ok':                True,
        'id':                servicio.id,
        'nombre':            servicio.nombre,
        'categoria':         servicio.categoria,
        'categoria_display': servicio.get_categoria_display(),
        'descripcion_corta': servicio.descripcion_corta,
        'activo':            servicio.activo,
        'total':             Servicio.objects.count(),
    })


# ── AJAX: eliminar un servicio ────────────────────────────────────────────────
@login_required
@solo_admin
@require_POST
def eliminar_ajax(request, serv_id):
    s = get_object_or_404(Servicio, id=serv_id)
    nombre = s.nombre
    s.delete()

    registrar(
        usuario=request.user,
        accion=f'Servicio eliminado: "{nombre}"',
        modulo='servicios',
        objeto_id=serv_id,
        request=request,
    )

    return JsonResponse({
        'ok':    True,
        'nombre': nombre,
        'total': Servicio.objects.count(),
    })


# ── AJAX: crear un nuevo servicio ─────────────────────────────────────────────
@login_required
@solo_admin
@require_POST
def crear_ajax(request):
    form = ServicioForm(request.POST, request.FILES)

    if not form.is_valid():
        errores = '; '.join(
            f'{f}: {", ".join(e)}' for f, e in form.errors.items()
        )
        return JsonResponse({'ok': False, 'error': errores}, status=400)

    servicio = form.save()

    registrar(
        usuario=request.user,
        accion=f'Servicio creado: "{servicio.nombre}" ({servicio.get_categoria_display()})',
        modulo='servicios',
        objeto_id=servicio.id,
        request=request,
    )

    return JsonResponse({
        'ok':                True,
        'id':                servicio.id,
        'nombre':            servicio.nombre,
        'categoria':         servicio.categoria,
        'categoria_display': servicio.get_categoria_display(),
        'descripcion_corta': servicio.descripcion_corta,
        'activo':            servicio.activo,
        'total':             Servicio.objects.count(),
        'activos':           Servicio.objects.filter(activo=True).count(),
    })
@login_required
@solo_admin
@require_POST
def toggle_activo_ajax(request, serv_id):
    s = get_object_or_404(Servicio, id=serv_id)
    s.activo = not s.activo
    s.save(update_fields=['activo'])

    registrar(
        usuario=request.user,
        accion=f'Servicio "{s.nombre}" marcado como {"publicado" if s.activo else "oculto"}',
        modulo='servicios',
        objeto_id=serv_id,
        request=request,
    )

    return JsonResponse({
        'ok': True,
        'activo': s.activo,
        'total': Servicio.objects.count(),
        'activos': Servicio.objects.filter(activo=True).count(),
    })