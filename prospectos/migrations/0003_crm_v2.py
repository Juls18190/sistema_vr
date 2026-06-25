from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prospectos', '002_crm_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='prospecto',
            name='tipo_registro',
            field=models.CharField(
                max_length=10,
                choices=[('prospecto', 'Prospecto'), ('cliente', 'Cliente')],
                default='prospecto',
                verbose_name='Tipo de registro',
            ),
        ),
        migrations.AddField(
            model_name='prospecto',
            name='servicios_interes',
            field=models.CharField(
                max_length=200,
                blank=True,
                default='',
                verbose_name='Servicios de interés',
            ),
        ),
        migrations.AddField(
            model_name='prospecto',
            name='promociones_actuales',
            field=models.CharField(
                max_length=200,
                blank=True,
                default='',
                verbose_name='Promociones actuales',
            ),
        ),
    ]