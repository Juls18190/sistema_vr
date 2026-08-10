from django import forms
from .models import Servicio


class ServicioForm(forms.ModelForm):

    class Meta:
        model = Servicio

        fields = [
            'nombre',
            'categoria',
            'descripcion_corta',
            'descripcion',
            'imagen',
            'orden',
            'activo',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'campo',
                'placeholder': 'Nombre del servicio'
            }),

            'categoria': forms.Select(attrs={
                'class': 'campo'
            }),

            'descripcion_corta': forms.TextInput(attrs={
                'class': 'campo',
                'placeholder': 'Descripción corta'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'campo',
                'rows': 4
            }),

            'imagen': forms.ClearableFileInput(attrs={
                'class': 'campo'
            }),

            'orden': forms.NumberInput(attrs={
                'class': 'campo'
            }),

            'activo': forms.CheckboxInput(attrs={
                'class': 'campo-check'
            }),
        }

        labels = {
            'nombre': 'Nombre',
            'categoria': 'Categoría',
            'descripcion_corta': 'Descripción corta',
            'descripcion': 'Descripción completa',
            'imagen': 'Imagen',
            'orden': 'Orden',
            'activo': 'Publicado',
        }