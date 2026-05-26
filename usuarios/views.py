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
