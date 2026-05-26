from django.db import models
from django.contrib.auth.models import User
 
class Cita(models.Model):
    nombre_cliente    = models.CharField(max_length=120)
    apellidos_cliente = models.CharField(max_length=120)
    correo            = models.EmailField()
    telefono          = models.CharField(max_length=20)
    fecha             = models.DateField()
    hora              = models.TimeField()
 
    MOTIVO_CHOICES = [
        ('seguro_vida', 'Seguro de vida'),
        ('medico',      'Gastos médicos mayores'),
        ('auto',        'Seguro de auto'),
        ('hogar',       'Seguro de hogar'),
        ('inversion',   'Inversión y ahorro'),
        ('empresa',     'Empresarial'),
        ('otro',        'Otro'),
    ]
    motivo      = models.CharField(max_length=50, choices=MOTIVO_CHOICES)
    motivo_otro = models.TextField(blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)
 
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada',  'Cancelada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
 
    # Asesor asignado (puede ser null si aún no se asigna)
    asesor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='citas_asignadas'
    )
    creada = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f'{self.nombre_cliente} {self.apellidos_cliente} — {self.fecha}'
 
    class Meta:
        verbose_name        = 'Cita'
        verbose_name_plural = 'Citas'
        ordering            = ['-creada']
