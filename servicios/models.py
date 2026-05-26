from django.db import models

class Servicio(models.Model):
    nombre = models.CharField(max_length=200)
    
    CATEGORIA_CHOICES = [
        ('personal', 'Seguros Personales'),
        ('inversion', 'Ahorro e Inversion'),
        ('empresarial', 'Empresarial'),
    ]
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField()
    descripcion_corta = models.CharField(max_length=300)
    icono_clase = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)
    def __str__(self):
        return self.nombre
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering =['orden']