from django.shortcuts import render
from .models import Servicio

def index(request):
    servicios = Servicio.objects.filter(activo=True).order_by('orden')
    return render(request, 'servicios/index.html', {'servicios': servicios})