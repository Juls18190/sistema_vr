from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Prospecto
from .forms  import ProspectoForm, ProspectoPublicoForm
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
def editar(request, prospecto_id):
    """Edita un prospecto existente."""
    prospecto = get_object_or_404(Prospecto, id=prospecto_id)
    if request.method == 'POST':
        form = ProspectoForm(request.POST, instance=prospecto)
        if form.is_valid():
            p = form.save()
            registrar(
                usuario=request.user,
                accion=f'Prospecto #{prospecto_id} ({p.nombre}) actualizado',
                modulo='prospectos',
                objeto_id=prospecto_id,
                request=request,
            )
            messages.success(request, f'Prospecto "{p.nombre}" actualizado.')
        else:
            errores = '; '.join(f'{f}: {", ".join(e)}' for f, e in form.errors.items())
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
