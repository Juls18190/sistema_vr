from django.db import models
from vacantes.models import Vacante


class Postulante(models.Model):

    ESTADO_CHOICES = [
        ('nuevo',       'Nuevo'),
        ('revisado',    'Revisado'),
        ('entrevista',  'Entrevista'),
        ('finalista',   'Finalista'),
        ('contratado',  'Contratado'),
        ('rechazado',   'Rechazado'),
    ]

    nombre   = models.CharField(max_length=120)
    correo   = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    cv       = models.FileField(upload_to='cvs/')

    vacante  = models.ForeignKey(
        Vacante,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postulantes'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='nuevo'
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas internas',
        help_text='Observaciones privadas del reclutador. No visibles para el postulante.'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_entrevista = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha y hora de entrevista',
        help_text='Se captura al marcar al postulante como "Entrevista".'
    )

    def __str__(self):
        return f'{self.nombre} — {self.vacante}'

    class Meta:
        verbose_name        = 'Postulante'
        verbose_name_plural = 'Postulantes'
        ordering            = ['-fecha']