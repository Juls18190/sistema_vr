_SERVICIO_LABELS = {
    'seguro_vida': 'Seguro de Vida',
    'medico':      'Gastos Médicos',
    'auto':        'Seguro de Auto',
    'hogar':       'Seguro de Hogar',
    'inversion':   'Inversión y Ahorro',
    'empresarial': 'Empresarial',
}


def _nombre_asesor(prospecto):
    a = prospecto.asesor_asignado
    if not a:
        return 'tu asesor de Grupo V&R Consultores'
    return a.get_full_name() or a.username


def _servicios_texto(prospecto, campo='servicios_interes'):
    csv = getattr(prospecto, campo, '') or ''
    nombres = [_SERVICIO_LABELS.get(v.strip(), v.strip()) for v in csv.split(',') if v.strip()]
    if not nombres:
        return 'nuestros servicios'
    if len(nombres) == 1:
        return nombres[0]
    return ', '.join(nombres[:-1]) + ' y ' + nombres[-1]


def primer_contacto(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Soy {_nombre_asesor(p)}, asesor de Grupo V&R Consultores.\n\n'
        f'Vi tu interés en {_servicios_texto(p)}. '
        f'¿Te gustaría que te comparta información y opciones disponibles?'
    )


def seguimiento_prospecto(p):
    return (
        f'Hola {p.nombre}, ¿cómo estás?\n'
        f'Soy {_nombre_asesor(p)}, de Grupo V&R Consultores. Quería dar seguimiento '
        f'a tu interés en {_servicios_texto(p)}. ¿Sigue siendo de tu interés que te apoye con esto?'
    )


def seguimiento_cotizacion(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Te escribo para dar seguimiento a la cotización de {_servicios_texto(p)} '
        f'que estuvimos platicando. ¿Tuviste oportunidad de revisarla?'
    )


def recordatorio_atencion(p):
    return (
        f'Hola {p.nombre}, un gusto saludarte.\n'
        f'Te recuerdo que quedamos en darle seguimiento a tu interés en {_servicios_texto(p)}. '
        f'¿Cuándo te vendría bien que platiquemos?'
    )


def no_responde(p):
    return (
        f'Hola {p.nombre}, espero te encuentres bien.\n'
        f'Te he buscado para platicarte sobre {_servicios_texto(p)}, pero no he tenido '
        f'respuesta. Quedo al pendiente por si en algún momento te interesa retomarlo.'
    )


def agradecimiento(p):
    return (
        f'¡Gracias, {p.nombre}! 🙏\n'
        f'Fue un gusto platicar contigo sobre {_servicios_texto(p)}. '
        f'Cualquier duda que tengas, aquí estoy para apoyarte.'
    )


def posterior_asesoria(p):
    return (
        f'Hola {p.nombre}, gracias por tu tiempo en la asesoría de hoy.\n'
        f'Quedo al pendiente de cualquier duda sobre {_servicios_texto(p)} que te haya '
        f'quedado pendiente.'
    )


def mensaje_servicio(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Te comparto información sobre {_servicios_texto(p)}, el servicio que solicitaste '
        f'en Grupo V&R Consultores. Cuéntame si tienes alguna duda.'
    )


def conversion_a_cliente(p):
    campo = 'promociones_actuales' if p.tipo_registro == 'cliente' else 'servicios_interes'
    return (
        f'¡Bienvenido(a) a Grupo V&R Consultores, {p.nombre}! 🎉\n'
        f'A partir de ahora formas parte de nuestros clientes, con {_servicios_texto(p, campo)}. '
        f'Cualquier cosa que necesites, cuenta conmigo, {_nombre_asesor(p)}.'
    )


# ── Registro de plantillas disponibles (clave → etiqueta, función) ───────────
PLANTILLAS = {
    'primer_contacto':       ('Primer contacto / presentación', primer_contacto),
    'seguimiento':            ('Seguimiento de prospecto',       seguimiento_prospecto),
    'seguimiento_cotizacion': ('Seguimiento de cotización',      seguimiento_cotizacion),
    'recordatorio':           ('Recordatorio de atención',       recordatorio_atencion),
    'no_responde':            ('Prospecto no responde',          no_responde),
    'agradecimiento':         ('Mensaje de agradecimiento',      agradecimiento),
    'posterior_asesoria':     ('Mensaje posterior a asesoría',   posterior_asesoria),
    'mensaje_servicio':       ('Mensaje sobre el servicio',      mensaje_servicio),
    'conversion':             ('Conversión a cliente',           conversion_a_cliente),
}


def generar_mensaje(clave, prospecto):
    """Devuelve el texto generado para una clave de plantilla y un prospecto dado."""
    entrada = PLANTILLAS.get(clave)
    if not entrada:
        return ''
    _, func = entrada
    return func(prospecto)