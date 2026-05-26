from django.contrib import admin
from .models import Prospecto

@admin.register(Prospecto)
class ProspectoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'correo', 'telefono', 'interes', 'estado']
    list_filter  = ['estado', 'interes']