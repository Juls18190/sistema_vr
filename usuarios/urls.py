from django.urls import path
from . import views
 
app_name = 'usuarios'
 
urlpatterns = [
    path('login/',            views.login_view,           name='login'),
    path('logout/',           views.logout_view,          name='logout'),
    path('password/ajax/',    views.cambiar_password_ajax, name='cambiar_password_ajax'),
]