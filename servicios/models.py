from django.db import models


class Servicio(models.Model):

    CATEGORIA_CHOICES = [
        ('personal', 'Seguros Personales'),
        ('inversion', 'Ahorro e Inversión'),
        ('empresarial', 'Empresarial'),
    ]

    nombre = models.CharField(max_length=200)

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES
    )

    descripcion_corta = models.CharField(max_length=300)

    descripcion = models.TextField()

    imagen = models.ImageField(
        upload_to='servicios/',
        blank=True,
        null=True
    )

    activo = models.BooleanField(default=True)

    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["orden"]