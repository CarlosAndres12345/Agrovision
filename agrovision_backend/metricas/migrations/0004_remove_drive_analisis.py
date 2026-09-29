from django.db import migrations, models


def eliminar_analisis_drive(apps, schema_editor):
    Analisis = apps.get_model('metricas', 'Analisis')
    Analisis.objects.filter(origen='drive_url').delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('metricas', '0003_analisis'),
    ]

    operations = [
        migrations.RunPython(eliminar_analisis_drive, noop_reverse),
        migrations.RemoveField(
            model_name='analisis',
            name='drive_url',
        ),
        migrations.AlterField(
            model_name='analisis',
            name='origen',
            field=models.CharField(
                choices=[('manual', 'Subida manual'), ('repositorio', 'Repositorio interno')],
                max_length=20,
            ),
        ),
    ]
