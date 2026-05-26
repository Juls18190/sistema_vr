from django.db import models
from django.contrib.auth.models import User


class Historial(models.Model):
    MODULO_CHOICES = [
        ('citas',       'Citas'),
        ('postulantes', 'Postulantes'),
        ('vacantes',    'Vacantes'),
        ('usuarios',    'Usuarios'),
        ('prospectos',  'Prospectos'),
        ('dashboard',   'Dashboard'),
    ]

    usuario   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial')
    accion    = models.CharField(max_length=300)
    modulo    = models.CharField(max_length=20, choices=MODULO_CHOICES)
    objeto_id = models.IntegerField(null=True, blank=True)
    fecha     = models.DateTimeField(auto_now_add=True)
    ip        = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f'{self.usuario} — {self.accion}'

    class Meta:
        verbose_name        = 'Historial'
        verbose_name_plural = 'Historial de actividad'
        ordering            = ['-fecha']


def registrar(usuario, accion, modulo, objeto_id=None, request=None):
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    Historial.objects.create(usuario=usuario, accion=accion, modulo=modulo, objeto_id=objeto_id, ip=ip)