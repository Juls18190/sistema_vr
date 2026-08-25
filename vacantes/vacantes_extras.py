"""
Template tags exclusivos para el LANDING PÚBLICO de vacantes.
No modifica ni sustituye la lógica de vacantes/views.py: es una
utilidad adicional y aislada, solo para filtrar por categoría en
la plantilla (necesaria para separar la pestaña "Todas" — que
muestra el queryset completo tal como ya lo entrega la vista — de
la pestaña "General", que debe mostrar únicamente las vacantes
cuyo público objetivo es literalmente "general").
"""
from django import template

register = template.Library()


@register.filter
def por_categoria(queryset, categoria):
    """Filtra una lista/queryset de Vacante por su publico_objetivo.
    Uso: {{ vacantes_general|por_categoria:'general' }}
    """
    if queryset is None:
        return []
    return [v for v in queryset if getattr(v, 'publico_objetivo', None) == categoria]
