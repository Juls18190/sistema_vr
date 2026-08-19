# postulantes/mensajes.py
#
# Generador de mensajes para el proceso de RECLUTAMIENTO Y SELECCIÓN DE
# PERSONAL (no confundir con citas de asesoría, que pertenecen al módulo
# Citas).
#
# Sigue el mismo patrón utilizado en prospectos/mensajes.py y citas/mensajes.py:
# cada plantilla es una función que recibe la instancia de Postulante y
# devuelve el texto ya personalizado, listo para enviarse por WhatsApp.

def _vacante_texto(postulante):
    if postulante.vacante:
        return postulante.vacante.titulo
    return 'la vacante a la que aplicaste'


def confirmacion_recepcion(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Soy parte del equipo de reclutamiento de Grupo V&R Consultores.\n\n'
        f'Confirmamos que recibimos tu postulación para {_vacante_texto(p)}. '
        f'En breve estaremos revisando tu perfil.'
    )


def invitacion_entrevista(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Nos gustaría invitarte a una entrevista para {_vacante_texto(p)}. '
        f'¿Qué día y horario tienes disponible?'
    )


def seguimiento_proceso(p):
    return (
        f'Hola {p.nombre}, ¿cómo estás?\n'
        f'Te escribo para darte seguimiento sobre tu proceso para {_vacante_texto(p)}. '
        f'Seguimos avanzando con la revisión de tu candidatura.'
    )


def solicitud_documentos(p):
    return (
        f'Hola {p.nombre} 👋\n'
        f'Para continuar con tu proceso de selección para {_vacante_texto(p)}, '
        f'¿podrías compartirnos la documentación pendiente cuando puedas?'
    )


def resultado_positivo(p):
    return (
        f'¡Felicidades, {p.nombre}! 🎉\n'
        f'Nos da mucho gusto informarte que avanzas a la siguiente etapa del proceso '
        f'para {_vacante_texto(p)}. Pronto te compartimos los siguientes pasos.'
    )


def resultado_negativo(p):
    return (
        f'Hola {p.nombre}, gracias por tu interés en {_vacante_texto(p)} '
        f'y por el tiempo dedicado a tu proceso con Grupo V&R Consultores.\n'
        f'En esta ocasión decidimos continuar con otro perfil, pero quedará tu '
        f'información para futuras vacantes.'
    )


# ── Registro de plantillas disponibles (clave → etiqueta, función) ───────────
PLANTILLAS = {
    'confirmacion_recepcion': ('Confirmación de recepción',  confirmacion_recepcion),
    'invitacion_entrevista':  ('Invitación a entrevista',    invitacion_entrevista),
    'seguimiento_proceso':    ('Seguimiento del proceso',    seguimiento_proceso),
    'solicitud_documentos':   ('Solicitud de documentos',    solicitud_documentos),
    'resultado_positivo':     ('Resultado positivo',         resultado_positivo),
    'resultado_negativo':     ('Resultado del proceso',      resultado_negativo),
}


def generar_mensaje(clave, postulante):
    """Devuelve el texto generado para una clave de plantilla y un postulante dado."""
    entrada = PLANTILLAS.get(clave)
    if not entrada:
        return ''
    _, func = entrada
    return func(postulante)
