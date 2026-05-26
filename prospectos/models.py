from django.db import models
from django.contrib.auth.models import User

class Prospecto(models.Model):
    nombre   = models.CharField(max_length=120)
    correo   = models.EmailField()
    telefono = models.CharField(max_length=20)
 
    INTERES_CHOICES = [
        ('seguro_vida', 'Seguro de vida'),
        ('medico',      'Gastos médicos'),
        ('auto',        'Seguro de auto'),
        ('hogar',       'Seguro de hogar'),
        ('inversion',   'Inversión y ahorro'),
        ('empresa',     'Empresarial'),
        ('general',     'Información general'),
    ]
    interes = models.CharField(max_length=30, choices=INTERES_CHOICES)
    mensaje = models.TextField(blank=True, null=True)
 
    ESTADO_CHOICES = [
        ('nuevo',      'Nuevo'),
        ('contactado', 'Contactado'),
        ('convertido', 'Convertido en cliente'),
        ('descartado', 'Descartado'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='nuevo')
 
    asesor_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prospectos_asignados'
    )
    fecha          = models.DateTimeField(auto_now_add=True)
    fecha_contacto = models.DateTimeField(null=True, blank=True)
    notas          = models.TextField(blank=True, null=True)
 
    def __str__(self):
        return f'{self.nombre} — {self.get_interes_display()}'
 
    class Meta:
        verbose_name        = 'Prospecto'
        verbose_name_plural = 'Prospectos'
        ordering            = ['-fecha']
