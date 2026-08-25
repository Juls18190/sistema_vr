from django.db import models
from django.contrib.auth.models import User


class TareaAgenda(models.Model):
    """
    Nota/tarea propia de un asesor (o admin) en el calendario, SIN relación
    a un cliente — para eso ya existe Cita. Ej.: "Llamar a lista de
    prospectos", "Revisar pólizas por vencer".

    El calendario combina estas tareas con las Citas del usuario al
    momento de renderizar; no hay relación de base de datos entre ambos
    modelos, para no tocar Cita en absoluto.
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tareas_agenda',
    )
    fecha = models.DateField()
    hora  = models.TimeField(null=True, blank=True)
    texto = models.CharField(max_length=255)

    completada = models.BooleanField(default=False)

    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora']
        indexes = [
            models.Index(fields=['usuario', 'fecha']),
        ]

    def __str__(self):
        return f'{self.fecha} — {self.texto[:40]} ({self.usuario.username})'
