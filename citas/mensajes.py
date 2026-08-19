# citas/mensajes.py
#
# Generador de mensajes para CITAS DE ASESORÍA (no confundir con entrevistas
# de reclutamiento, que pertenecen al módulo Postulantes).
#
# Sigue el mismo patrón utilizado en prospectos/mensajes.py:
# cada plantilla es una función que recibe la instancia de Cita y devuelve
# el texto ya personalizado, listo para enviarse por WhatsApp.

_MOTIVO_LABELS = {
    'seguro_vida': 'Seguro de Vida',
    'medico':      'Gastos Médicos Mayores',
    'auto':        'Seguro de Auto',
    'hogar':       'Seguro de Hogar',
    'inversion':   'Inversión y Ahorro',
    'empresa':     'Empresarial',
    'otro':        'tu consulta',
}


def _nombre_cliente(cita):
    return f'{cita.nombre_cliente} {cita.apellidos_cliente}'.strip()


def _nombre_asesor(cita):
    a = cita.asesor
    if not a:
        return 'tu asesor de Grupo V&R Consultores'
    return a.get_full_name() or a.username


def _motivo_texto(cita):
    if cita.motivo == 'otro' and cita.motivo_otro:
        return cita.motivo_otro
    return _MOTIVO_LABELS.get(cita.motivo, 'tu asesoría')


def _fecha_hora_texto(cita):
    try:
        fecha = cita.fecha.strftime('%d/%m/%Y')
    except AttributeError:
        fecha = str(cita.fecha)
    try:
        hora = cita.hora.strftime('%H:%M')
    except AttributeError:
        hora = str(cita.hora)
    return f'{fecha} a las {hora}'


def confirmacion_cita(c):
    return (
        f'Hola {c.nombre_cliente} 👋\n'
        f'Soy {_nombre_asesor(c)}, de Grupo V&R Consultores.\n\n'
        f'Te confirmo tu cita de asesoría sobre {_motivo_texto(c)} '
        f'para el {_fecha_hora_texto(c)}. ¡Te espero!'
    )


def recordatorio_cita(c):
    return (
        f'Hola {c.nombre_cliente}, ¿cómo estás?\n'
        f'Te recuerdo tu cita de asesoría sobre {_motivo_texto(c)} '
        f'programada para el {_fecha_hora_texto(c)}. '
        f'Cualquier cambio, avísame con confianza.'
    )


def reagendar_cita(c):
    return (
        f'Hola {c.nombre_cliente} 👋\n'
        f'Te escribo respecto a tu cita de asesoría sobre {_motivo_texto(c)}, '
        f'programada originalmente para el {_fecha_hora_texto(c)}. '
        f'¿Te gustaría que la reagendemos para otro día u horario?'
    )


def seguimiento_posterior(c):
    return (
        f'Hola {c.nombre_cliente}, gracias por tu tiempo en la asesoría de {_motivo_texto(c)}.\n'
        f'Quedo al pendiente por si te quedó alguna duda o si quieres que avancemos '
        f'con los siguientes pasos.'
    )


def cancelacion_cita(c):
    return (
        f'Hola {c.nombre_cliente}, te escribo de parte de Grupo V&R Consultores.\n'
        f'Tu cita de asesoría sobre {_motivo_texto(c)} del {_fecha_hora_texto(c)} '
        f'ha sido cancelada. Si deseas agendar una nueva fecha, quedo a tus órdenes.'
    )


# ── Registro de plantillas disponibles (clave → etiqueta, función) ───────────
PLANTILLAS = {
    'confirmacion':  ('Confirmación de cita',      confirmacion_cita),
    'recordatorio':  ('Recordatorio de cita',      recordatorio_cita),
    'reagendar':     ('Reagendar cita',            reagendar_cita),
    'seguimiento':   ('Seguimiento posterior',     seguimiento_posterior),
    'cancelacion':   ('Cancelación de cita',       cancelacion_cita),
}


def generar_mensaje(clave, cita):
    """Devuelve el texto generado para una clave de plantilla y una cita dada."""
    entrada = PLANTILLAS.get(clave)
    if not entrada:
        return ''
    _, func = entrada
    return func(cita)
