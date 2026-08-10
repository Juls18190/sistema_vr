from django.contrib import admin
from django.utils.html import format_html

from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):

    list_display = (
        "preview",
        "nombre",
        "categoria",
        "activo",
        "orden",
    )

    list_editable = (
        "activo",
        "orden",
    )

    list_filter = (
        "categoria",
        "activo",
    )

    search_fields = (
        "nombre",
    )

    def preview(self, obj):

        if obj.imagen:

            return format_html(
                '<img src="{}" width="90" style="border-radius:8px;">',
                obj.imagen.url
            )

        return "Sin imagen"

    preview.short_description = "Imagen"