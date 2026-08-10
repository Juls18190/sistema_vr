from django.shortcuts import render
from servicios.models import Servicio
from citas.models import Cita
from postulantes.models import Postulante
from prospectos.models import Prospecto
from vacantes.models import Vacante


def home(request):
    servicios = Servicio.objects.filter(activo=True).order_by('orden')

    # Vacantes destacadas: solo activas, las más recientes primero
    Vacante.sincronizar_vencidas()
    vacantes_destacadas = Vacante.objects.filter(estado='activa').order_by('-creada')[:6]

    context = {
        'servicios': servicios,
        'vacantes_destacadas': vacantes_destacadas,
        # Stats reales para el dashboard público
        'total_postulantes': Postulante.objects.count(),
        'total_citas': Cita.objects.count(),
        'total_prospectos': Prospecto.objects.count(),
    }
    return render(request, 'inicio/index.html', context)