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
        ('vencida',  'Vencida'),
    ]

    PUBLICO_OBJETIVO_CHOICES = [
        ('general',        'General'),
        ('estudiantes',    'Estudiantes'),
        ('jubilados',      'Jubilados'),
        ('amas_casa',      'Amas de casa'),
        ('profesionistas', 'Profesionistas'),
    ]
    PUBLICO_OBJETIVO_CHOICES = [
        ('general',        'General'),
        ('estudiantes',    'Estudiantes'),
        ('jubilados',      'Jubilados'),
        ('amas_casa',      'Amas de casa'),
        ('profesionistas', 'Profesionistas'),
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

    # ── Público objetivo ─────────────────────────────────────────────────────
    publico_objetivo = models.CharField(
        'Público objetivo',
        max_length=20,
        choices=PUBLICO_OBJETIVO_CHOICES,
        default='general',
    )

    # ── Público objetivo ─────────────────────────────────────────────────────
    publico_objetivo = models.CharField(
        'Público objetivo',
        max_length=20,
        choices=PUBLICO_OBJETIVO_CHOICES,
        default='general',
    )
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
        # Estado automático por fecha límite: solo se toca si NO fue
        # puesta manualmente en pausada/cerrada — esas siempre se respetan.
        from datetime import date
        if self.estado not in ('pausada', 'cerrada'):
            vencida = bool(self.fecha_limite) and self.fecha_limite < date.today()
            self.estado = 'vencida' if vencida else 'activa'

        # Sincronizar campo legacy `activa` con `estado`
        self.activa = (self.estado == 'activa')
        super().save(*args, **kwargs)

    @classmethod
    def sincronizar_vencidas(cls):
        """Autocorrige en la base de datos las vacantes cuya fecha límite
        ya pasó (o volvió a ser futura) sin que nadie las haya editado.
        Nunca toca pausada/cerrada. Se llama al abrir cualquier listado."""
        from datetime import date
        from django.db.models import Q
        hoy = date.today()
        cls.objects.filter(estado='activa', fecha_limite__lt=hoy).update(estado='vencida', activa=False)
        cls.objects.filter(estado='vencida').filter(
            Q(fecha_limite__isnull=True) | Q(fecha_limite__gte=hoy)
        ).update(estado='activa', activa=True)

    def __str__(self):
        return self.titulo

    @property
    def esta_vencida(self):
        """True si la fecha límite ya pasó. No cambia `estado` ni se elimina la vacante."""
        from datetime import date
        return bool(self.fecha_limite) and self.fecha_limite < date.today()

    class Meta:
        verbose_name        = 'Vacante'
        verbose_name_plural = 'Vacantes'
        ordering            = ['-creada']