from django import forms
from django.contrib.auth.models import User
from .models import Prospecto


# ── Formulario PÚBLICO (sitio web) ────────────────────────────────────────────
class ProspectoPublicoForm(forms.ModelForm):
    """Solo campos visibles al visitante del sitio."""
    class Meta:
        model  = Prospecto
        fields = ['nombre', 'correo', 'telefono', 'interes', 'mensaje']
        widgets = {
            'nombre':   forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'correo':   forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '782-000-0000'}),
            'interes':  forms.Select(),
            'mensaje':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Cuéntanos cómo podemos ayudarte…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mensaje'].required = False


# ── Formulario ADMIN (panel interno) ─────────────────────────────────────────
class ProspectoForm(forms.ModelForm):
    class Meta:
        model  = Prospecto
        fields = [
            'nombre', 'correo', 'telefono', 'interes',
            'mensaje', 'estado', 'asesor_asignado',
            'fecha_contacto', 'notas',
        ]
        widgets = {
            'nombre':   forms.TextInput(attrs={'placeholder': 'Nombre completo', 'class': 'campo'}),
            'correo':   forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com', 'class': 'campo'}),
            'telefono': forms.TextInput(attrs={'placeholder': '782-000-0000', 'class': 'campo'}),
            'interes':  forms.Select(attrs={'class': 'campo'}),
            'mensaje':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mensaje o notas iniciales…', 'class': 'campo'}),
            'estado':   forms.Select(attrs={'class': 'campo'}),
            'asesor_asignado': forms.Select(attrs={'class': 'campo'}),
            'fecha_contacto':  forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'campo'}),
            'notas':    forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas de seguimiento…', 'class': 'campo'}),
        }
        labels = {
            'nombre':           'Nombre completo *',
            'correo':           'Correo electrónico *',
            'telefono':         'Teléfono *',
            'interes':          'Interés / Servicio *',
            'mensaje':          'Mensaje inicial',
            'estado':           'Estado *',
            'asesor_asignado':  'Asesor asignado',
            'fecha_contacto':   'Fecha de contacto',
            'notas':            'Notas internas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asesor_asignado'].queryset = User.objects.filter(is_active=True)
        self.fields['asesor_asignado'].empty_label = '— Sin asignar —'
        self.fields['asesor_asignado'].required = False
        self.fields['fecha_contacto'].required = False
        self.fields['notas'].required = False
        self.fields['mensaje'].required = False