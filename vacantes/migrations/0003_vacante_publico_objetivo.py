# Generated manually to match Django 5.2.13 migration style used in this project

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacantes', '0002_vacante_actualizada_vacante_estado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacante',
            name='publico_objetivo',
            field=models.CharField(
                choices=[
                    ('general', 'General'),
                    ('estudiantes', 'Estudiantes'),
                    ('jubilados', 'Jubilados'),
                    ('amas_casa', 'Amas de casa'),
                    ('profesionistas', 'Profesionistas'),
                ],
                default='general',
                max_length=20,
                verbose_name='Público objetivo',
            ),
        ),
        migrations.AlterField(
            model_name='vacante',
            name='estado',
            field=models.CharField(
                choices=[
                    ('activa', 'Activa'),
                    ('pausada', 'Pausada'),
                    ('cerrada', 'Cerrada'),
                    ('vencida', 'Vencida'),
                ],
                default='activa',
                max_length=10,
            ),
        ),
    ]