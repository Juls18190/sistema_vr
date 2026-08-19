from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Citas
    path('citas/ajax/',      views.reporte_citas_ajax,   name='citas_ajax'),
    path('citas/pdf/',       views.exportar_citas_pdf,   name='citas_pdf'),
    path('citas/excel/',     views.exportar_citas_excel, name='citas_excel'),
    path('asesores/ajax/',   views.asesores_ajax,        name='asesores_ajax'),

    # Prospectos
    path('prospectos/ajax/',  views.reporte_prospectos_ajax,    name='prospectos_ajax'),
    path('prospectos/pdf/',   views.exportar_prospectos_pdf,    name='prospectos_pdf'),
    path('prospectos/excel/', views.exportar_prospectos_excel,  name='prospectos_excel'),

    # Postulantes
    path('postulantes/ajax/',  views.reporte_postulantes_ajax,   name='postulantes_ajax'),
    path('postulantes/pdf/',   views.exportar_postulantes_pdf,   name='postulantes_pdf'),
    path('postulantes/excel/', views.exportar_postulantes_excel, name='postulantes_excel'),
    path('vacantes-lista/ajax/', views.vacantes_lista_ajax,      name='vacantes_lista_ajax'),

    # Vacantes
    path('vacantes/ajax/',  views.reporte_vacantes_ajax,   name='vacantes_ajax'),
    path('vacantes/pdf/',   views.exportar_vacantes_pdf,   name='vacantes_pdf'),
    path('vacantes/excel/', views.exportar_vacantes_excel, name='vacantes_excel'),

    # Servicios
    path('servicios/ajax/',  views.reporte_servicios_ajax,   name='servicios_ajax'),
    path('servicios/pdf/',   views.exportar_servicios_pdf,   name='servicios_pdf'),
    path('servicios/excel/', views.exportar_servicios_excel, name='servicios_excel'),

    # Resumen general
    path('resumen/ajax/',  views.resumen_general_ajax,          name='resumen_ajax'),
    path('resumen/pdf/',   views.exportar_resumen_general_pdf,  name='resumen_pdf'),
    path('resumen/excel/', views.exportar_resumen_general_excel, name='resumen_excel'),
]