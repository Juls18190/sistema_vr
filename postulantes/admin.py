from django.contrib import admin
from .models import Postulante

@admin.register(Postulante)
class PostulanteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'correo', 'telefono', 'estado', 'fecha']
    list_filter  = ['estado']
    search_fields = ['nombre', 'correo']