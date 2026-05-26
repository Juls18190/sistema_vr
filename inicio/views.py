from django.shortcuts import render
from vacantes.models import Vacante
from servicios.models import Servicio
from citas.models import Cita
from postulantes.models import Postulante
from prospectos.models import Prospecto


def home(request):
    vacantes = Vacante.objects.filter(estado='activa').order_by('-creada')[:6]
    servicios = Servicio.objects.filter(activo=True).order_by('orden')
    context = {
        'vacantes': vacantes,
        'servicios': servicios,
        # Stats reales para el dashboard público
        'total_postulantes': Postulante.objects.count(),
        'total_citas': Cita.objects.count(),
        'total_prospectos': Prospecto.objects.count(),
        'vacantes_activas_count': Vacante.objects.filter(estado='activa').count(),
    }
    return render(request, 'inicio/index.html', context)
