from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prospectos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Campos nuevos en Prospecto
        migrations.AddField(
            model_name='prospecto',
            name='empresa_actual',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Empresa actual'),
        ),
        migrations.AddField(
            model_name='prospecto',
            name='es_referido',
            field=models.BooleanField(default=False, verbose_name='¿Es referido?'),
        ),
        migrations.AddField(
            model_name='prospecto',
            name='nombre_referente',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='Nombre del referente'),
        ),
        migrations.AddField(
            model_name='prospecto',
            name='archivo_poliza',
            field=models.FileField(blank=True, null=True, upload_to='prospectos/polizas/', verbose_name='Póliza actual (PDF)'),
        ),
        # Nuevo modelo SeguimientoProspecto
        migrations.CreateModel(
            name='SeguimientoProspecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comentario', models.TextField(verbose_name='Comentario')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('asesor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguimientos_realizados',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('prospecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seguimientos',
                    to='prospectos.prospecto',
                )),
            ],
            options={
                'verbose_name': 'Seguimiento',
                'verbose_name_plural': 'Seguimientos',
                'ordering': ['-fecha'],
            },
        ),
    ]