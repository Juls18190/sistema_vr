from django.contrib import admin
from .models import Prospecto, SeguimientoProspecto


@admin.register(Prospecto)
class ProspectoAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'correo', 'telefono', 'interes', 'estado', 'es_referido', 'empresa_actual']
    list_filter   = ['estado', 'interes', 'es_referido']
    search_fields = ['nombre', 'correo', 'empresa_actual', 'nombre_referente']


@admin.register(SeguimientoProspecto)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display  = ['prospecto', 'asesor', 'fecha']
    list_filter   = ['asesor']
    search_fields = ['prospecto__nombre', 'comentario']
    readonly_fields = ['fecha']