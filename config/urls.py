from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',       admin.site.urls),
    path('',             include('inicio.urls')),        # ← usa inicio/views.py::home con contexto correcto
    path('servicios/',   include('servicios.urls')),
    path('vacantes/',    include('vacantes.urls')),
    path('citas/',       include('citas.urls')),
    path('postulantes/', include('postulantes.urls')),
    path('dashboard/',   include('dashboard.urls')),
    path('usuarios/',    include('usuarios.urls')),
    path('prospectos/',  include('prospectos.urls')),
    path('reportes/',    include('reportes.urls')),
    path('historial/',   include('historial.urls')),
    path('agenda/',      include('agenda.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)