from django.contrib import admin
from .models import Cita

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display  = ['nombre_cliente', 'apellidos_cliente', 'fecha', 'hora', 'motivo', 'estado']
    list_filter   = ['estado', 'fecha']
    search_fields = ['nombre_cliente', 'correo']