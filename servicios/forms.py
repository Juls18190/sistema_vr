from django import forms
from .models import Servicio


class ServicioForm(forms.ModelForm):
    class Meta:
        model  = Servicio
        fields = [
            'nombre', 'categoria', 'descripcion_corta',
            'descripcion', 'icono_clase', 'orden', 'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Seguro de vida, Ahorro universitario…',
                'class': 'campo',
            }),
            'categoria': forms.Select(attrs={'class': 'campo'}),
            'descripcion_corta': forms.TextInput(attrs={
                'placeholder': 'Resumen breve visible en tarjetas (máx. 300 car.)',
                'class': 'campo',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descripción completa del servicio…',
                'class': 'campo',
            }),
            'icono_clase': forms.TextInput(attrs={
                'placeholder': 'Ej. fa-shield-alt (Font Awesome class)',
                'class': 'campo',
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'campo',
                'min': 0,
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'campo-check'}),
        }
        labels = {
            'nombre':           'Nombre del servicio *',
            'categoria':        'Categoría *',
            'descripcion_corta':'Descripción corta *',
            'descripcion':      'Descripción completa *',
            'icono_clase':      'Clase de ícono (opcional)',
            'orden':            'Orden de aparición',
            'activo':           'Publicado (visible en el sitio)',
        }