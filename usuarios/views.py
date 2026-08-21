from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse

from .models import PerfilUsuario
from .permisos import solo_admin, es_admin
from historial.models import registrar


def login_view(request):
    # Si ya tiene sesión activa, ir directo al dashboard
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            # authenticate() regresa None tanto si la contraseña es
            # incorrecta como si el usuario existe pero está inactivo
            # (ModelBackend.user_can_authenticate() filtra por is_active).
            # Distinguimos ese caso para dar un mensaje claro, sin revelar
            # si la contraseña enviada era correcta o no.
            existe_inactivo = User.objects.filter(
                username__iexact=username, is_active=False
            ).exists()
            if existe_inactivo:
                error = 'Esta cuenta está desactivada. Contacta a un administrador.'
            else:
                error = 'Usuario o contraseña incorrectos'

    return render(request, 'usuarios/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('/usuarios/login/')


@login_required
def cambiar_password_ajax(request):
    
    """Cambia la contraseña del usuario autenticado vía AJAX.

    Restringido a Superadmin/Administrador: los Asesores no pueden cambiar
    su propia contraseña desde el dashboard (política del negocio, no un
    tema de UI — por eso se valida aquí y no solo ocultando el botón).
    """
    from django.http import JsonResponse
    from django.contrib.auth import update_session_auth_hash

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    if not es_admin(request.user):
        return JsonResponse(
            {'ok': False, 'error': 'No tienes permiso para cambiar tu contraseña. Contacta a un administrador.'},
            status=403,
        )

    actual     = request.POST.get('password_actual', '')
    nueva      = request.POST.get('password_nueva', '')
    confirmacion = request.POST.get('password_confirmacion', '')

    if not actual or not nueva or not confirmacion:
        return JsonResponse({'ok': False, 'error': 'Todos los campos son obligatorios.'})

    if not request.user.check_password(actual):
        return JsonResponse({'ok': False, 'error': 'La contraseña actual es incorrecta.'})

    if nueva != confirmacion:
        return JsonResponse({'ok': False, 'error': 'La nueva contraseña y su confirmación no coinciden.'})

    if len(nueva) < 8:
        return JsonResponse({'ok': False, 'error': 'La nueva contraseña debe tener al menos 8 caracteres.'})

    request.user.set_password(nueva)
    request.user.save()
    update_session_auth_hash(request, request.user)  # mantiene la sesión activa

    return JsonResponse({'ok': True, 'mensaje': 'Contraseña actualizada correctamente.'})


# ═══════════════════════════════════════════════════════════════════════════
# FASE C — Gestión de usuarios desde el Dashboard
#
# Reglas de permisos (ver usuarios/permisos.py::solo_admin):
#   - Superadmin (is_superuser) y Administrador (perfil.rol == 'admin') pueden
#     ver/crear/editar/activar/desactivar usuarios.
#   - Asesor es rechazado por el decorador @solo_admin en TODOS los casos
#     (petición AJAX -> 403 JSON; petición normal -> redirect + mensaje).
#     Esta protección es la misma que ya usan Postulantes/Vacantes/Servicios,
#     no depende de que el botón esté oculto en el HTML.
#
# is_superuser / is_staff NUNCA se leen desde el request: el formulario de
# esta interfaz solo puede asignar los roles definidos en
# PerfilUsuario.ROL_CHOICES ('admin' / 'asesor'). El Superadmin se sigue
# gestionando exclusivamente desde /admin/.
# ═══════════════════════════════════════════════════════════════════════════

def _serializar_usuario(u):
    """Representación JSON única de un usuario, usada por las 4 vistas AJAX
    de esta sección y consumida por el JS del dashboard para construir/
    actualizar la tarjeta (ucard) sin recargar la página."""
    perfil = getattr(u, 'perfil', None)
    if u.is_superuser:
        rol, rol_display = 'superadmin', 'Superadmin'
    elif perfil and perfil.rol == 'admin':
        rol, rol_display = 'admin', 'Administrador'
    else:
        rol, rol_display = 'asesor', 'Asesor'

    return {
        'id':               u.id,
        'first_name':       u.first_name,
        'last_name':        u.last_name,
        'nombre_completo':  u.get_full_name() or u.username,
        'username':         u.username,
        'email':            u.email or '',
        'telefono':         (perfil.telefono if perfil else '') or '',
        'rol':              rol,
        'rol_display':      rol_display,
        'is_superuser':     u.is_superuser,
        'is_active':        u.is_active,
        'fecha_registro':   u.date_joined.strftime('%d/%m/%Y'),
        'ultimo_acceso':    u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Nunca',
    }


# ── AJAX: crear usuario desde el dashboard ────────────────────────────────
@login_required
@solo_admin
def crear_usuario_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    nombre    = request.POST.get('first_name', '').strip()
    apellidos = request.POST.get('last_name', '').strip()
    username  = request.POST.get('username', '').strip()
    email     = request.POST.get('email', '').strip()
    telefono  = request.POST.get('telefono', '').strip()
    rol       = request.POST.get('rol', '').strip()
    password  = request.POST.get('password', '')
    password2 = request.POST.get('password_confirmacion', '')

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)
    if not username:
        return JsonResponse({'ok': False, 'error': 'El nombre de usuario es obligatorio.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({'ok': False, 'error': 'El nombre de usuario ya existe.'}, status=400)

    # ── Correo: obligatorio, con formato válido y único (se usará más
    #    adelante para recuperación de contraseña; en esta fase solo se
    #    valida y almacena) ──────────────────────────────────────────────
    if not email:
        return JsonResponse({'ok': False, 'error': 'El correo electrónico es obligatorio.'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'ok': False, 'error': 'El correo electrónico no tiene un formato válido.'}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'ok': False, 'error': 'El correo electrónico ya está registrado.'}, status=400)

    roles_validos = dict(PerfilUsuario.ROL_CHOICES)  # {'admin': ..., 'asesor': ...} — nunca incluye Superadmin
    if rol not in roles_validos:
        return JsonResponse({'ok': False, 'error': 'Rol no válido.'}, status=400)

    if not password or not password2:
        return JsonResponse({'ok': False, 'error': 'La contraseña y su confirmación son obligatorias.'}, status=400)
    if password != password2:
        return JsonResponse({'ok': False, 'error': 'Las contraseñas no coinciden.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'ok': False, 'error': 'La contraseña debe tener al menos 8 caracteres.'}, status=400)

    with transaction.atomic():
        nuevo_usuario = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellidos,
        )
        # No se leen is_superuser / is_staff del request bajo ninguna
        # circunstancia: se crean con sus valores por defecto (False).
        PerfilUsuario.objects.create(user=nuevo_usuario, rol=rol, telefono=telefono)

    registrar(
        usuario=request.user,
        accion=f'Usuario "{nuevo_usuario.get_full_name() or nuevo_usuario.username}" creado con rol {roles_validos[rol]}',
        modulo='usuarios',
        objeto_id=nuevo_usuario.id,
        request=request,
    )

    return JsonResponse({'ok': True, 'usuario': _serializar_usuario(nuevo_usuario)})


# ── AJAX: detalle de usuario (para modal "Ver" y para precargar "Editar") ─
@login_required
@solo_admin
def detalle_usuario_ajax(request, user_id):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)
    usuario = get_object_or_404(User.objects.select_related('perfil'), id=user_id)
    return JsonResponse({'ok': True, 'usuario': _serializar_usuario(usuario)})


# ── AJAX: editar usuario ──────────────────────────────────────────────────
@login_required
@solo_admin
def editar_usuario_ajax(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    usuario = get_object_or_404(User.objects.select_related('perfil'), id=user_id)

    nombre    = request.POST.get('first_name', '').strip()
    apellidos = request.POST.get('last_name', '').strip()
    username  = request.POST.get('username', '').strip()
    email     = request.POST.get('email', '').strip()
    telefono  = request.POST.get('telefono', '').strip()
    rol       = request.POST.get('rol', '').strip()
    password  = request.POST.get('password', '')
    password2 = request.POST.get('password_confirmacion', '')

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)
    if not username:
        return JsonResponse({'ok': False, 'error': 'El nombre de usuario es obligatorio.'}, status=400)
    if User.objects.exclude(id=usuario.id).filter(username__iexact=username).exists():
        return JsonResponse({'ok': False, 'error': 'El nombre de usuario ya existe.'}, status=400)

    if not email:
        return JsonResponse({'ok': False, 'error': 'El correo electrónico es obligatorio.'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'ok': False, 'error': 'El correo electrónico no tiene un formato válido.'}, status=400)
    if User.objects.exclude(id=usuario.id).filter(email__iexact=email).exists():
        return JsonResponse({'ok': False, 'error': 'El correo electrónico ya está registrado.'}, status=400)

    if password or password2:
        if password != password2:
            return JsonResponse({'ok': False, 'error': 'Las contraseñas no coinciden.'}, status=400)
        if len(password) < 8:
            return JsonResponse({'ok': False, 'error': 'La contraseña debe tener al menos 8 caracteres.'}, status=400)

    roles_validos = dict(PerfilUsuario.ROL_CHOICES)
    cambios = []

    # El Superadmin (is_superuser=True) no gestiona su rol desde este panel:
    # ese control sigue siendo exclusivo de is_superuser vía /admin/. Para
    # cualquier otro usuario, el rol enviado debe ser uno de los válidos.
    perfil = getattr(usuario, 'perfil', None)

    if not usuario.is_superuser:
        if rol not in roles_validos:
            return JsonResponse({'ok': False, 'error': 'Rol no válido.'}, status=400)
        if perfil is None:
            perfil = PerfilUsuario.objects.create(user=usuario, rol=rol, telefono=telefono)
            cambios.append(f'rol asignado como "{roles_validos[rol]}"')
        else:
            if perfil.rol != rol:
                cambios.append(f'rol de "{roles_validos.get(perfil.rol, perfil.rol)}" a "{roles_validos[rol]}"')
                perfil.rol = rol
            if perfil.telefono != telefono:
                cambios.append('teléfono')
            perfil.telefono = telefono
            perfil.save(update_fields=['rol', 'telefono'])
    elif perfil is not None and perfil.telefono != telefono:
        # El Superadmin sí puede guardar su propio teléfono, aunque su rol
        # no se edite desde aquí.
        cambios.append('teléfono')
        perfil.telefono = telefono
        perfil.save(update_fields=['telefono'])

    if usuario.first_name != nombre:
        cambios.append('nombre')
    if usuario.last_name != apellidos:
        cambios.append('apellidos')
    if usuario.username != username:
        cambios.append('nombre de usuario')
    if usuario.email != email:
        cambios.append('correo electrónico')

    usuario.first_name = nombre
    usuario.last_name  = apellidos
    usuario.username   = username
    usuario.email      = email

    if password:
        usuario.set_password(password)
        cambios.append('contraseña')

    usuario.save()

    if cambios:
        registrar(
            usuario=request.user,
            accion=f'Usuario "{usuario.get_full_name() or usuario.username}" editado ({", ".join(cambios)})',
            modulo='usuarios',
            objeto_id=usuario.id,
            request=request,
        )

    return JsonResponse({'ok': True, 'usuario': _serializar_usuario(usuario)})


# ── AJAX: activar / desactivar usuario (nunca elimina físicamente) ───────
@login_required
@solo_admin
def cambiar_estado_usuario_ajax(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    usuario = get_object_or_404(User, id=user_id)

    # Protección contra pérdida accidental del acceso principal: los
    # Superadministradores no se activan/desactivan desde este panel.
    if usuario.is_superuser:
        return JsonResponse(
            {'ok': False, 'error': 'Los Superadministradores no se pueden activar/desactivar desde este panel.'},
            status=400,
        )

    # Prevenir auto-desactivación: nadie puede desactivar su propia cuenta.
    if usuario.id == request.user.id:
        return JsonResponse({'ok': False, 'error': 'No puedes desactivar tu propia cuenta.'}, status=400)

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])

    accion_txt = 'activado' if usuario.is_active else 'desactivado'
    registrar(
        usuario=request.user,
        accion=f'Usuario "{usuario.get_full_name() or usuario.username}" {accion_txt}',
        modulo='usuarios',
        objeto_id=usuario.id,
        request=request,
    )

    return JsonResponse({'ok': True, 'usuario': _serializar_usuario(usuario)})