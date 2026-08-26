#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

# Crea el primer superusuario si no existe todavía. Necesario porque el
# plan Free de Render no da acceso SSH ni "one-off jobs" para correr
# `createsuperuser` a mano. Solo actúa si las 3 variables están definidas
# y el usuario no existe ya (seguro correrlo en cada deploy).
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
if username and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superusuario {username} creado.')
"
