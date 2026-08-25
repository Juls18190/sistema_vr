# asignacion/servicios.py
#
# Punto único de lógica para la asignación automática de asesores a citas
# nuevas. Se llama desde citas/views.py::agendar() (formulario público) —
# no se duplica en ninguna otra vista.
#
# Reglas (ver conversación de diseño):
#   1. Si ya existe un Prospecto con ese correo y tiene asesor_asignado,
#      se conserva ese asesor. NUNCA vuelve a entrar al round-robin.
#   2. Si la automatización está desactivada, no se asigna nada (se
#      mantiene el comportamiento actual: asesor=None).
#   3. Si no hay asesores activos disponibles, no se asigna nada.
#   4. Si el prospecto es nuevo, se toma el siguiente asesor del
#      round-robin, se guarda en el turno y se usa para la cita.
#
# El orden de los asesores es estable: PerfilUsuario.rol == 'asesor' +
# User.is_active, ordenado por user_id (nunca cambia). No se agrega
# ningún campo nuevo a PerfilUsuario ni a User.

from django.contrib.auth.models import User
from django.db import transaction

from .models import ConfiguracionAsignacion


def _asesores_activos_ordenados():
    """
    Queryset estable de usuarios con rol='asesor' y cuenta activa,
    ordenado por id de usuario. Misma lógica de "activo" que ya usa el
    resto del proyecto (User.is_active), no PerfilUsuario.activo (que no
    se usa en ningún otro punto del código).
    """
    return (
        User.objects
        .filter(is_active=True, perfil__rol='asesor')
        .order_by('id')
    )


def _siguiente_asesor(config, asesores):
    """
    Devuelve el siguiente asesor de la lista, a partir de
    config.ultimo_asesor_id. Si el último asesor asignado ya no está en
    la lista (fue desactivado o cambió de rol), se reinicia desde el
    primero — sin alterar las asignaciones ya hechas anteriormente.
    """
    asesores = list(asesores)
    if not asesores:
        return None

    if config.ultimo_asesor_id is None:
        return asesores[0]

    ids = [a.id for a in asesores]
    try:
        idx = ids.index(config.ultimo_asesor_id)
    except ValueError:
        return asesores[0]

    return asesores[(idx + 1) % len(asesores)]


def obtener_asesor_para(correo):
    """
    Punto de entrada único. Devuelve el User asesor que debe usarse para
    una cita nueva de este correo, o None si no aplica (automatización
    desactivada, sin asesores disponibles, o correo vacío).

    NO crea la Cita. NO crea el Prospecto — eso lo sigue haciendo el
    flujo existente (asignar_y_crear_prospecto_ajax) cuando el admin lo
    decide; el formulario público (citas/views.py::agendar) nunca creó
    un Prospecto automáticamente, y esta función respeta ese
    comportamiento tal cual está hoy.

    Como agendar() no crea Prospecto, "ya tiene asesor" se resuelve en
    dos niveles, en este orden:
      1. Existe un Prospecto con este correo y tiene asesor_asignado
         → se conserva ese asesor (fuente de verdad principal, la
         misma que ya usa _sincronizar_prospecto_por_asesor).
      2. No hay Prospecto todavía, pero ya existe una Cita previa con
         este mismo correo que tiene asesor asignado → se conserva ese
         asesor. Esto cubre el caso real de una misma persona agendando
         dos citas por el formulario público antes de que un admin la
         convierta en Prospecto; sin este paso, la segunda cita
         volvería a entrar al round-robin y podría tocarle otro asesor.
      3. Ninguno de los dos existe → prospecto nuevo, entra al
         round-robin.
    """
    from prospectos.models import Prospecto
    from citas.models import Cita

    if not correo:
        return None

    correo = correo.strip()
    if not correo:
        return None

    # 1. Prospecto existente con asesor ya asignado → se conserva, sin
    #    tocar el turno del round-robin.
    prospecto = Prospecto.objects.filter(correo=correo).first()
    if prospecto and prospecto.asesor_asignado_id:
        return prospecto.asesor_asignado

    # 2. Sin Prospecto todavía, pero ya hay una Cita previa de este
    #    correo con asesor asignado → se conserva, sin tocar el turno.
    cita_previa = (
        Cita.objects
        .filter(correo=correo, asesor__isnull=False)
        .order_by('-creada')
        .first()
    )
    if cita_previa:
        return cita_previa.asesor

    with transaction.atomic():
        config = (
            ConfiguracionAsignacion.objects
            .select_for_update()
            .get(pk=ConfiguracionAsignacion.obtener().pk)
        )

        if not config.activo:
            return None

        asesor = _siguiente_asesor(config, _asesores_activos_ordenados())
        if asesor is None:
            return None

        config.ultimo_asesor = asesor
        config.save(update_fields=['ultimo_asesor', 'actualizado'])

        # Si el prospecto ya existe pero no tenía asesor, se lo asignamos.
        # Si no existe, NO lo creamos aquí (eso sigue siendo
        # responsabilidad del flujo admin actual) — solo devolvemos el
        # asesor para que la Cita se cree con él.
        if prospecto and not prospecto.asesor_asignado_id:
            prospecto.asesor_asignado = asesor
            prospecto.save(update_fields=['asesor_asignado'])

        return asesor
