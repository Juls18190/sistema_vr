from django.db import models


class Vacante(models.Model):

    MODALIDAD_CHOICES = [
        ('completo', 'Tiempo completo'),
        ('medio',    'Medio tiempo'),
        ('remoto',   'Remoto'),
        ('hibrido',  'Híbrido'),
    ]

    ESTADO_CHOICES = [
        ('activa',   'Activa'),
        ('pausada',  'Pausada'),
        ('cerrada',  'Cerrada'),
    ]

    # ── Datos básicos ─────────────────────────────────────────────────────────
    titulo      = models.CharField('Título del puesto',   max_length=200)
    area        = models.CharField('Área / Departamento', max_length=100)
    descripcion = models.TextField('Descripción del puesto')
    requisitos  = models.TextField('Requisitos',          blank=True, null=True)
    ubicacion   = models.CharField('Ubicación',           max_length=150, blank=True, null=True)

    # ── Condiciones ───────────────────────────────────────────────────────────
    modalidad   = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='completo')
    sueldo      = models.CharField('Sueldo / Rango salarial', max_length=100, blank=True, null=True,
                                   help_text='Ej: $8,000 – $12,000 MXN mensual')

    # ── Estado ────────────────────────────────────────────────────────────────
    estado      = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activa')
    activa      = models.BooleanField(default=True)   # ← compatibilidad con código anterior

    # ── Archivos ──────────────────────────────────────────────────────────────
    pdf_convocatoria = models.FileField(
        'PDF de convocatoria',
        upload_to='vacantes/pdfs/',
        blank=True, null=True
    )
    imagen = models.ImageField(
        'Imagen de portada',
        upload_to='vacantes/imagenes/',
        blank=True, null=True
    )

    # ── Fechas ────────────────────────────────────────────────────────────────
    fecha_limite = models.DateField('Fecha límite de postulación', blank=True, null=True)
    creada       = models.DateTimeField(auto_now_add=True)
    actualizada  = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sincronizar campo legacy `activa` con `estado`
        self.activa = (self.estado == 'activa')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name        = 'Vacante'
        verbose_name_plural = 'Vacantes'
        ordering            = ['-creada']