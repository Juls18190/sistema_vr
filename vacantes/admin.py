from django.contrib import admin
from .models import Vacante


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display  = ['titulo', 'area', 'modalidad', 'estado', 'fecha_limite', 'creada']
    list_filter   = ['estado', 'modalidad']
    search_fields = ['titulo', 'area', 'descripcion']
    list_editable = ['estado']
    ordering      = ['-creada']