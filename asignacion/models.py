from django.conf import settings
from django.db import models


class ConfiguracionAsignacion(models.Model):
    """
    Configuración única (patrón singleton, siempre pk=1) de la asignación
    automática de asesores para citas nuevas.

    No se guarda aquí la lista de "asesores participantes": se calcula en
    vivo a partir de PerfilUsuario.rol == 'asesor' + User.is_active, que es
    la misma lógica que ya usa el resto del proyecto (ver
    usuarios/permisos.py y los selectores de asesor en el Dashboard). Así,
    desactivar/reactivar un usuario asesor ya lo saca/mete del reparto sin
    necesidad de un campo o tabla adicional.

    `ultimo_asesor` guarda el turno del round-robin: el último asesor al
    que se le asignó un prospecto nuevo. Se usa junto con
    transaction.atomic() + select_for_update() en asignacion/servicios.py
    para evitar condiciones de carrera entre citas simultáneas.
    """
    activo = models.BooleanField(
        default=False,
        verbose_name='Asignación automática activada',
    )
    ultimo_asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Último asesor asignado (turno round-robin)',
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de asignación automática'
        verbose_name_plural = 'Configuración de asignación automática'

    def __str__(self):
        estado = 'activada' if self.activo else 'desactivada'
        return f'Asignación automática ({estado})'

    @classmethod
    def obtener(cls):
        """Devuelve (creando si hace falta) la única fila de configuración."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
