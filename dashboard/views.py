from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from citas.models       import Cita
from postulantes.models import Postulante
from vacantes.models    import Vacante
from prospectos.models  import Prospecto
from servicios.models   import Servicio
from historial.models   import Historial
from usuarios.models    import PerfilUsuario


def _datos_mensuales():
    MESES_ES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    hoy = timezone.now()
    periodos = []
    for i in range(5, -1, -1):
        mes = hoy.month - i
        año = hoy.year
        while mes <= 0:
            mes += 12
            año -= 1
        periodos.append((año, mes))

    citas_qs = (
        Cita.objects
        .annotate(mes=TruncMonth('creada'))
        .values('mes')
        .annotate(total=Count('id'))
    )
    citas_map = {(r['mes'].year, r['mes'].month): r['total'] for r in citas_qs}

    posts_qs = (
        Postulante.objects
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
    )
    posts_map = {(r['mes'].year, r['mes'].month): r['total'] for r in posts_qs}

    meses_labels = [MESES_ES[m - 1] for _, m in periodos]
    citas_data   = [citas_map.get(p, 0) for p in periodos]
    posts_data   = [posts_map.get(p, 0) for p in periodos]

    return meses_labels, citas_data, posts_data


@login_required(login_url='/usuarios/login/')
def index(request):
    try:
        meses_labels, citas_data, posts_data = _datos_mensuales()

        hoy = timezone.now()
        MESES_ES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                    'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        hoy_str = f'{MESES_ES[hoy.month - 1]} {hoy.year}'

        usuarios = User.objects.select_related('perfil').filter(is_active=True).order_by('first_name', 'username')

        # Historial: una sola query con select_related, limitado a 15 entradas
        historial_reciente = (
            Historial.objects
            .select_related('usuario')
            .order_by('-fecha')[:15]
        )

        # Citas cuya fecha de cita (no de creación) es hoy
        citas_hoy = Cita.objects.filter(fecha=hoy.date()).count()

        contexto = {
            # ── KPIs principales (tarjetas del dashboard) ──────────────────
            'citas_pendientes':         Cita.objects.filter(estado='pendiente').count(),
            'citas_hoy':                citas_hoy,
            'postulantes_nuevos':       Postulante.objects.filter(estado='nuevo').count(),
            'vacantes_activas':         Vacante.objects.filter(estado='activa').count(),
            'vacantes_pausadas':        Vacante.objects.filter(estado='pausada').count(),
            'vacantes_cerradas':        Vacante.objects.filter(estado='cerrada').count(),
            'vacantes_total':           Vacante.objects.count(),
            'prospectos_nuevos':        Prospecto.objects.filter(estado='nuevo').count(),

            # ── Postulantes — 6 estados (Fase 1) ──────────────────────────
            'postulantes_total':        Postulante.objects.count(),
            'postulantes_revisados':    Postulante.objects.filter(estado='revisado').count(),
            'postulantes_entrevista':   Postulante.objects.filter(estado='entrevista').count(),
            'postulantes_finalistas':   Postulante.objects.filter(estado='finalista').count(),
            'postulantes_contratados':  Postulante.objects.filter(estado='contratado').count(),
            'postulantes_rechazados':   Postulante.objects.filter(estado='rechazado').count(),

            # ── Citas ──────────────────────────────────────────────────────
            'citas':                    Cita.objects.select_related('asesor').order_by('-creada')[:50],
            'citas_total':              Cita.objects.count(),
            'citas_confirmadas':        Cita.objects.filter(estado='confirmada').count(),
            'citas_completadas':        Cita.objects.filter(estado='completada').count(),
            'citas_canceladas':         Cita.objects.filter(estado='cancelada').count(),

            # ── Vacantes ──────────────────────────────────────────────────
            'vacantes': Vacante.objects.annotate(
                num_postulantes=Count('postulantes')
            ).order_by('-creada')[:50],
            'vacantes_pausadas':        Vacante.objects.filter(estado='pausada').count(),
            'vacantes_cerradas':        Vacante.objects.filter(estado='cerrada').count(),

            # ── Postulantes tabla ──────────────────────────────────────────
            'postulantes':              Postulante.objects.select_related('vacante').order_by('-fecha')[:50],

            # ── Prospectos ────────────────────────────────────────────────
            'prospectos':               Prospecto.objects.select_related('asesor_asignado').order_by('-fecha')[:50],
            'prospectos_total':         Prospecto.objects.count(),
            'prospectos_contactados':   Prospecto.objects.filter(estado='contactado').count(),
            'prospectos_convertidos':   Prospecto.objects.filter(estado='convertido').count(),
            'prospectos_descartados':   Prospecto.objects.filter(estado='descartado').count(),

            # ── Servicios ─────────────────────────────────────────────────
            'servicios':                Servicio.objects.all().order_by('orden'),
            'servicios_total':          Servicio.objects.count(),
            'servicios_activos':        Servicio.objects.filter(activo=True).count(),
            'servicios_ocultos':        Servicio.objects.filter(activo=False).count(),
            'servicios_personal':       Servicio.objects.filter(categoria='personal').count(),
            'servicios_inversion':      Servicio.objects.filter(categoria='inversion').count(),
            'servicios_empresarial':    Servicio.objects.filter(categoria='empresarial').count(),

            # ── Usuarios ──────────────────────────────────────────────────
            'usuarios':                 usuarios,
            'usuarios_total':           User.objects.filter(is_active=True).count(),

            # ── Historial ─────────────────────────────────────────────────
            'historial_reciente':       historial_reciente,
            'historial_total':          Historial.objects.count(),

            # ── Listas para selects ───────────────────────────────────────
            'vacantes_activas_lista':   Vacante.objects.filter(activa=True).order_by('titulo'),
            'asesores':                 User.objects.filter(is_active=True).order_by('first_name', 'username'),

            # ── Datos para gráficas ───────────────────────────────────────
            'chart_meses':     meses_labels,
            'chart_citas':     citas_data,
            'chart_posts':     posts_data,
            'chart_doughnut':  [
                Cita.objects.filter(estado='pendiente').count(),
                Cita.objects.filter(estado='confirmada').count(),
                Cita.objects.filter(estado='completada').count(),
                Cita.objects.filter(estado='cancelada').count(),
            ],

            # ── Citas del día (panel lateral) ─────────────────────────────
            'citas_dia': Cita.objects.filter(
                fecha=hoy.date()
            ).select_related('asesor').order_by('hora'),

            # ── Utilidades ────────────────────────────────────────────────
            'hoy':     hoy.date(),
            'hoy_str': hoy_str,
            'usuario': request.user,
        }

    except Exception as e:
        contexto = {
            'citas_pendientes': 0, 'citas_hoy': 0,
            'postulantes_nuevos': 0, 'vacantes_activas': 0,
            'vacantes_total': 0, 'prospectos_nuevos': 0,
            'postulantes_total': 0, 'postulantes_revisados': 0,
            'postulantes_entrevista': 0, 'postulantes_finalistas': 0,
            'postulantes_contratados': 0, 'postulantes_rechazados': 0,
            'citas': [], 'citas_total': 0,
            'citas_confirmadas': 0, 'citas_completadas': 0, 'citas_canceladas': 0,
            'vacantes': [], 'vacantes_pausadas': 0, 'vacantes_cerradas': 0,
            'postulantes': [],
            'prospectos': [], 'prospectos_total': 0,
            'prospectos_contactados': 0, 'prospectos_convertidos': 0,
            'prospectos_descartados': 0,
            'servicios': [], 'servicios_total': 0, 'servicios_activos': 0,
            'servicios_ocultos': 0, 'servicios_personal': 0,
            'servicios_inversion': 0, 'servicios_empresarial': 0,
            'usuarios': [], 'usuarios_total': 0,
            'historial_reciente': [], 'historial_total': 0,
            'vacantes_activas_lista': [], 'asesores': [],
            'chart_meses':    ['Ene','Feb','Mar','Abr','May','Jun'],
            'chart_citas':    [0, 0, 0, 0, 0, 0],
            'chart_posts':    [0, 0, 0, 0, 0, 0],
            'chart_doughnut': [0, 0, 0, 0],
            'citas_dia': [],
            'hoy': timezone.now().date(),
            'hoy_str': '',
            'usuario': request.user,
            'error_dashboard': str(e),
        }
        

    return render(request, 'dashboard/index.html', contexto)

@login_required
def kpis_ajax(request):
    """Devuelve KPIs y actividad reciente filtrados por periodo."""
    from datetime import datetime, time as time_obj, timedelta

    periodo = request.GET.get('periodo', 'mes')
    hoy     = timezone.now().date()

    rangos = {
        'hoy':    timezone.make_aware(datetime.combine(hoy, time_obj.min)),
        'semana': timezone.make_aware(datetime.combine(
                      hoy - timedelta(days=hoy.weekday()), time_obj.min)),
        'mes':    timezone.make_aware(datetime.combine(
                      hoy.replace(day=1), time_obj.min)),
        'año':    timezone.make_aware(datetime.combine(
                      hoy.replace(month=1, day=1), time_obj.min)),
    }
    inicio = rangos.get(periodo, rangos['mes'])

    # KPIs filtrados por periodo
    citas_periodo      = Cita.objects.filter(creada__gte=inicio).count()
    postulantes_periodo = Postulante.objects.filter(fecha__gte=inicio).count()
    prospectos_periodo  = Prospecto.objects.filter(fecha__gte=inicio).count()
    vacantes_periodo    = Vacante.objects.filter(creada__gte=inicio).count()

    # Actividad reciente filtrada por periodo
    historial_qs = (
        Historial.objects
        .select_related('usuario')
        .filter(fecha__gte=inicio)
        .order_by('-fecha')[:15]
    )
    actividad = []
    colores = {
        'postulantes': '#3b82f6',
        'citas':       '#22c55e',
        'vacantes':    '#8b5cf6',
        'prospectos':  '#f59e0b',
        'usuarios':    '#0d9488',
    }
    for h in historial_qs:
        actividad.append({
            'accion':  h.accion,
            'modulo':  h.modulo,
            'color':   colores.get(h.modulo, '#94a3b8'),
            'usuario': (h.usuario.get_full_name() or h.usuario.username) if h.usuario else 'Sistema',
            'fecha':   h.fecha.strftime('%d/%m/%Y %H:%M'),
        })

    # Citas del día (siempre son de hoy, independiente del filtro)
    citas_hoy_lista = []
    for c in Cita.objects.filter(fecha=hoy).select_related('asesor').order_by('hora'):
        citas_hoy_lista.append({
            'nombre':  f'{c.nombre_cliente} {c.apellidos_cliente}',
            'hora':    c.hora.strftime('%H:%M'),
            'motivo':  c.get_motivo_display(),
            'estado':  c.estado,
            'asesor':  (c.asesor.get_full_name() or c.asesor.username) if c.asesor else '—',
        })

    return JsonResponse({
        'ok':      True,
        'periodo': periodo,
        'kpis': {
            'citas':      citas_periodo,
            'post':       postulantes_periodo,
            'prosp':      prospectos_periodo,
            'vac':        vacantes_periodo,
        },
        'actividad':   actividad,
        'citas_hoy':   citas_hoy_lista,
        'total_hoy':   len(citas_hoy_lista),
    })

@login_required
def cambiar_estado_ajax(request, post_id):

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método inválido'})

    postulante = get_object_or_404(Postulante, id=post_id)

    nuevo_estado = request.POST.get('estado')

    estados_validos = [
        'nuevo',
        'revisado',
        'entrevista',
        'finalista',
        'contratado',
        'rechazado'
    ]

    if nuevo_estado not in estados_validos:
        return JsonResponse({'ok': False, 'error': 'Estado inválido'})

    postulante.estado = nuevo_estado
    postulante.save()

    return JsonResponse({
        'ok': True,
        'estado': postulante.estado
    })