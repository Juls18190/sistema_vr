# usuarios/permisos.py
#
# Helper de permisos por rol, reutilizable entre apps.
# Sigue el mismo criterio ya usado en prospectos/views.py::_rol() y
# citas/views.py: Superadmin (is_superuser) o Administrador
# (PerfilUsuario.rol == 'admin') tienen acceso completo; el Asesor no.
#
# Se usa principalmente para bloquear a nivel de vista módulos completos
# que el Asesor no debe poder tocar (Postulantes, Vacantes, Servicios).
# Para permisos por objeto (p. ej. "solo mis citas") cada app mantiene su
# propio helper local, como ya ocurre con _verificar_acceso_prospecto().

from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


def es_admin(user):
    """
    True si el usuario es Superadmin o Administrador.
    Usa getattr con fallback para evitar errores si el perfil no existe.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.es_admin)


def solo_admin(view_func):
    """
    Decorador para restringir una vista a Superadmin/Administrador.
    Debe usarse junto con @login_required (encima de este decorador).

    Si el usuario autenticado es Asesor:
      - Petición AJAX (header X-Requested-With: XMLHttpRequest) → 403 JSON.
      - Petición normal → redirección segura al Dashboard con mensaje de error.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not es_admin(request.user):
            es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if es_ajax:
                return JsonResponse(
                    {'ok': False, 'error': 'No tienes permiso para acceder a este módulo.'},
                    status=403,
                )
            messages.error(request, 'No tienes permiso para acceder a ese módulo.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return _wrapped
