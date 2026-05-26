# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    ROL_CHOICES = [
        ('admin',  'Administrador'),
        ('asesor', 'Asesor'),
    ]
    rol      = models.CharField(max_length=10, choices=ROL_CHOICES, default='asesor')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto     = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    activo   = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_rol_display()})'

    @property
    def es_admin(self):
        return self.rol == 'admin'

    @property
    def es_asesor(self):
        return self.rol == 'asesor'

    class Meta:
        verbose_name        = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'