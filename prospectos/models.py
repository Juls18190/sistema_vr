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

   # ── Campos CRM heredados (se mantienen por compatibilidad) ─────────────────
    empresa_actual   = models.CharField(max_length=200, blank=True, null=True,
                                        verbose_name='Empresa actual')
    es_referido      = models.BooleanField(default=False,
                                           verbose_name='¿Es referido?')
    nombre_referente = models.CharField(max_length=120, blank=True, null=True,
                                        verbose_name='Nombre del referente')
    archivo_poliza   = models.FileField(upload_to='prospectos/polizas/', blank=True, null=True,
                                        verbose_name='Póliza actual (PDF)')

    # ── Campos CRM nuevos ──────────────────────────────────────────────────────
    TIPO_REGISTRO_CHOICES = [
        ('prospecto', 'Prospecto'),
        ('cliente',   'Cliente'),
    ]
    tipo_registro        = models.CharField(max_length=10,
                                            choices=TIPO_REGISTRO_CHOICES,
                                            default='prospecto',
                                            verbose_name='Tipo de registro')
    # Almacenados como CSV: "seguro_vida,medico,auto"
    servicios_interes    = models.CharField(max_length=200, blank=True, default='',
                                            verbose_name='Servicios de interés')
    promociones_actuales = models.CharField(max_length=200, blank=True, default='',
                                            verbose_name='Promociones actuales')
    
    def __str__(self):
        return f'{self.nombre} — {self.get_interes_display()}'

    class Meta:
        verbose_name        = 'Prospecto'
        verbose_name_plural = 'Prospectos'
        ordering            = ['-fecha']


class SeguimientoProspecto(models.Model):
    prospecto  = models.ForeignKey(
        Prospecto,
        on_delete=models.CASCADE,
        related_name='seguimientos'
    )
    asesor     = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='seguimientos_realizados'
    )
    comentario = models.TextField(verbose_name='Comentario')
    fecha      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Seguimiento #{self.id} — {self.prospecto.nombre}'

    class Meta:
        verbose_name        = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'
        ordering            = ['-fecha']