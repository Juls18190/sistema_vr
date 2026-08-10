from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


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
            error = 'Usuario o contraseña incorrectos'

    return render(request, 'usuarios/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('/usuarios/login/')


@login_required
def cambiar_password_ajax(request):
    
    """Cambia la contraseña del usuario autenticado vía AJAX."""
    from django.http import JsonResponse
    from django.contrib.auth import update_session_auth_hash

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

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