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

def _qs_prospectos(user):
    """
    Devuelve el queryset base de Prospecto visible para este usuario.
    Admin/superuser → todos. Asesor → solo los asignados a él.
    """
    perfil   = getattr(user, 'perfil', None)
    es_admin = perfil.es_admin if perfil else user.is_superuser
    if es_admin:
        return Prospecto.objects.all()
    return Prospecto.objects.filter(asesor_asignado=user)


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
        Vacante.sincronizar_vencidas()
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
            'prospectos_nuevos':        _qs_prospectos(request.user).filter(estado='nuevo').count(),

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

            # ── Prospectos — filtrados por rol ────────────────────────────
            'prospectos':               _qs_prospectos(request.user).select_related('asesor_asignado').order_by('-fecha')[:50],
            'prospectos_total':         _qs_prospectos(request.user).count(),
            'prospectos_contactados':   _qs_prospectos(request.user).filter(estado='contactado').count(),
            'prospectos_convertidos':   _qs_prospectos(request.user).filter(estado='convertido').count(),
            'prospectos_descartados':   _qs_prospectos(request.user).filter(estado='descartado').count(),

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

# ── Notificaciones en tiempo real ─────────────────────────────────────────────
# Estructura de cada notificación:
#   tipo        → identificador de categoría ('cita_hoy', 'postulante_nuevo', etc.)
#   titulo      → texto corto del encabezado
#   mensaje     → descripción legible
#   prioridad   → 'alta' | 'media' | 'informativa'
#   canales     → lista de canales habilitados en fases futuras ['dashboard', 'email', 'whatsapp']
#   accion_nav  → sección del dashboard a la que navega el botón (para nav() en el JS)
#   accion_url  → URL alternativa si la acción sale del dashboard (puede ser None)
#
# FASE 2: cuando se implemente el modelo Notificacion, esta función
# seguirá calculando las mismas queries pero además creará registros
# persistentes y los enviará por email/WhatsApp según `canales`.

def _calcular_notificaciones(usuario):
    """
    Calcula notificaciones en tiempo real con ORM.
    Devuelve lista ordenada por prioridad (alta → media → informativa).
    """
    from datetime import timedelta
    from django.db.models import Max

    hoy      = timezone.now().date()
    items    = []

    PRIORIDAD_ORDEN = {'alta': 0, 'media': 1, 'informativa': 2}

    # ── 1. Citas pendientes o confirmadas de HOY ───────────────────────────────
    citas_hoy = Cita.objects.filter(
        fecha=hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('hora')

    for c in citas_hoy:
        hora_str = c.hora.strftime('%H:%M')
        items.append({
            'tipo':       'cita_hoy',
            'titulo':     f'Cita a las {hora_str}',
            'mensaje':    f'{c.nombre_cliente} {c.apellidos_cliente} — {c.get_motivo_display()}',
            'prioridad':  'alta',
            'canales':    ['dashboard'],          # Fase 2: agregar 'email', 'whatsapp'
            'accion_nav': 'citas',
            'accion_url': None,
        })

    # ── 2. Postulantes en estado 'nuevo' (sin revisar) ─────────────────────────
    post_nuevos = Postulante.objects.filter(estado='nuevo').count()
    if post_nuevos > 0:
        items.append({
            'tipo':       'postulante_nuevo',
            'titulo':     'Postulantes sin revisar',
            'mensaje':    f'{post_nuevos} postulante{"s" if post_nuevos > 1 else ""} esperando revisión',
            'prioridad':  'media',
            'canales':    ['dashboard'],
            'accion_nav': 'postulantes',
            'accion_url': None,
        })

# ── 3. Prospectos sin ningún seguimiento (filtrado por rol) ───────────────
    qs_prosp = _qs_prospectos(usuario)
    sin_seguimiento = qs_prosp.filter(
        seguimientos__isnull=True,
        estado__in=['nuevo', 'contactado']
    ).count()
    if sin_seguimiento > 0:
        items.append({
            'tipo':       'prospecto_sin_seguimiento',
            'titulo':     'Prospectos sin seguimiento',
            'mensaje':    f'{sin_seguimiento} prospecto{"s" if sin_seguimiento > 1 else ""} sin ningún contacto registrado',
            'prioridad':  'media',
            'canales':    ['dashboard'],
            'accion_nav': 'prospectos',
            'accion_url': None,
        })

    # ── 4. Prospectos sin seguimiento en los últimos 7 días (por rol) ─────────
    hace_7_dias = timezone.now() - timedelta(days=7)
    con_seguimiento_reciente = (
        qs_prosp
        .filter(seguimientos__fecha__gte=hace_7_dias)
        .values_list('id', flat=True)
    )
    sin_seguimiento_reciente = qs_prosp.filter(
        estado__in=['nuevo', 'contactado'],
        seguimientos__isnull=False,
    ).exclude(id__in=con_seguimiento_reciente).count()
    if sin_seguimiento_reciente > 0:
        items.append({
            'tipo':       'prospecto_seguimiento_tardio',
            'titulo':     'Seguimientos atrasados',
            'mensaje':    f'{sin_seguimiento_reciente} prospecto{"s" if sin_seguimiento_reciente > 1 else ""} sin seguimiento en los últimos 7 días',
            'prioridad':  'media',
            'canales':    ['dashboard'],
            'accion_nav': 'prospectos',
            'accion_url': None,
        })

    # ── . Vacantes activas por vencer (próximos 7 días) ──────────────────────
    en_7_dias = hoy + timedelta(days=7)
    vac_por_vencer = Vacante.objects.filter(
        estado='activa',
        fecha_limite__isnull=False,
        fecha_limite__lte=en_7_dias,
        fecha_limite__gte=hoy,
    )
    for v in vac_por_vencer:
        dias_restantes = (v.fecha_limite - hoy).days
        if dias_restantes == 0:
            tiempo_msg = 'vence HOY'
            prioridad  = 'alta'
        elif dias_restantes == 1:
            tiempo_msg = 'vence mañana'
            prioridad  = 'alta'
        else:
            tiempo_msg = f'vence en {dias_restantes} días'
            prioridad  = 'media'

        items.append({
            'tipo':       'vacante_por_vencer',
            'titulo':     'Vacante próxima a cerrar',
            'mensaje':    f'"{v.titulo}" {tiempo_msg}',
            'prioridad':  prioridad,
            'canales':    ['dashboard'],
            'accion_nav': 'vacantes',
            'accion_url': None,
        })

    # ── Ordenar: alta → media → informativa ───────────────────────────────────
    items.sort(key=lambda x: PRIORIDAD_ORDEN.get(x['prioridad'], 99))

    return items


@login_required
def notificaciones_ajax(request):
    """Endpoint AJAX para el panel de notificaciones del dashboard."""
    items = _calcular_notificaciones(request.user)

    # Etiqueta visual por prioridad
    prioridad_labels = {
        'alta':        {'label': 'Alta',        'color': '#dc2626', 'bg': '#fee2e2'},
        'media':       {'label': 'Media',       'color': '#d97706', 'bg': '#fef3c7'},
        'informativa': {'label': 'Informativa', 'color': '#2563eb', 'bg': '#dbeafe'},
    }
    for item in items:
        item['prioridad_meta'] = prioridad_labels.get(item['prioridad'], prioridad_labels['informativa'])

    return JsonResponse({
        'ok':    True,
        'total': len(items),
        'items': items,
    })

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
    prospectos_periodo  = _qs_prospectos(request.user).filter(fecha__gte=inicio).count()
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