from django.contrib import admin
from .models import TareaAgenda


@admin.register(TareaAgenda)
class TareaAgendaAdmin(admin.ModelAdmin):
    list_display  = ['usuario', 'fecha', 'hora', 'texto', 'completada']
    list_filter   = ['completada', 'fecha']
    search_fields = ['texto', 'usuario__username', 'usuario__first_name', 'usuario__last_name']
