from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/',            views.login_view,           name='login'),
    path('logout/',           views.logout_view,          name='logout'),
    path('password/ajax/',    views.cambiar_password_ajax, name='cambiar_password_ajax'),

    # ── FASE D: Recuperación de contraseña ───────────────────────────────
    # Flujo estándar de Django (django.contrib.auth.views), no un sistema
    # casero de tokens. El token es de un solo uso y expira solo
    # (PASSWORD_RESET_TIMEOUT, por defecto 3 días en Django).
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='usuarios/password_reset_form.html',
            email_template_name='usuarios/password_reset_email.txt',
            subject_template_name='usuarios/password_reset_subject.txt',
            success_url='/usuarios/password-reset/enviado/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='usuarios/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/confirmar/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url='/usuarios/password-reset/completado/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='usuarios/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),

    # ── FASE C: Gestión de usuarios desde el Dashboard ──────────────────
    # Protegidas en backend por @login_required + @solo_admin (ver
    # usuarios/permisos.py). Un Asesor recibe 403 (AJAX) o redirect
    # (petición normal) aunque acceda a estas URLs directamente.
    path('crear/ajax/',                views.crear_usuario_ajax,          name='crear_usuario_ajax'),
    path('<int:user_id>/detalle/ajax/', views.detalle_usuario_ajax,       name='detalle_usuario_ajax'),
    path('<int:user_id>/editar/ajax/',  views.editar_usuario_ajax,        name='editar_usuario_ajax'),
    path('<int:user_id>/estado/ajax/',  views.cambiar_estado_usuario_ajax, name='cambiar_estado_usuario_ajax'),
]