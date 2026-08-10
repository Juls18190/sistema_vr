from django import forms
from .models import Vacante


class VacanteForm(forms.ModelForm):
    class Meta:
        model  = Vacante
        fields = [
            'titulo', 'area', 'descripcion', 'requisitos',
            'ubicacion', 'modalidad', 'sueldo', 'estado',
            'publico_objetivo', 'fecha_limite', 'pdf_convocatoria', 'imagen',
        ]
        widgets = {
            'titulo':      forms.TextInput(attrs={
                'placeholder': 'Ej. Asesor financiero senior',
                'class': 'campo',
            }),
            'area':        forms.TextInput(attrs={
                'placeholder': 'Ej. Ventas, Consultoría, Operaciones…',
                'class': 'campo',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe las responsabilidades del puesto…',
                'class': 'campo',
            }),
            'requisitos':  forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Experiencia mínima, estudios, habilidades requeridas…',
                'class': 'campo',
            }),
            'ubicacion':   forms.TextInput(attrs={
                'placeholder': 'Ej. Poza Rica, Ver. / Remoto',
                'class': 'campo',
            }),
            'modalidad':   forms.Select(attrs={'class': 'campo'}),
            'sueldo':      forms.TextInput(attrs={
                'placeholder': 'Ej. $8,000 – $12,000 MXN mensual',
                'class': 'campo',
            }),
            'estado':      forms.Select(attrs={'class': 'campo'}),
            'publico_objetivo': forms.Select(attrs={'class': 'campo'}),
            'fecha_limite':forms.DateInput(attrs={
                'type': 'date',
                'class': 'campo',
            }),
            'pdf_convocatoria': forms.FileInput(attrs={'class': 'campo', 'accept': '.pdf'}),
            'imagen':      forms.FileInput(attrs={'class': 'campo', 'accept': 'image/*'}),
        }
        labels = {
            'titulo':           'Título del puesto *',
            'area':             'Área / Departamento *',
            'descripcion':      'Descripción *',
            'requisitos':       'Requisitos',
            'ubicacion':        'Ubicación',
            'modalidad':        'Modalidad *',
            'sueldo':           'Sueldo / Rango salarial',
            'estado':           'Estado de la vacante *',
            'publico_objetivo': 'Público objetivo *',
            'fecha_limite':     'Fecha límite',
            'pdf_convocatoria': 'PDF de convocatoria',
            'imagen':           'Imagen de portada',
        }

    def clean_pdf_convocatoria(self):
        pdf = self.cleaned_data.get('pdf_convocatoria')
        if pdf and hasattr(pdf, 'name'):
            if not pdf.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Solo se permiten archivos PDF.')
            if pdf.size > 10 * 1024 * 1024:   # 10 MB
                raise forms.ValidationError('El PDF no puede superar 10 MB.')
        return pdf

    def clean_imagen(self):
        img = self.cleaned_data.get('imagen')
        if img and hasattr(img, 'name'):
            ext = img.name.lower().split('.')[-1]
            if ext not in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
                raise forms.ValidationError('Formatos permitidos: JPG, PNG, WEBP, GIF.')
            if img.size > 5 * 1024 * 1024:    # 5 MB
                raise forms.ValidationError('La imagen no puede superar 5 MB.')
        return img