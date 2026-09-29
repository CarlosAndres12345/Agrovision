# Paso 3/3: ahora que 0006 copió todo a ImagenCultivo, se eliminan las FKs
# viejas de ImagenRepositorio y se renombran los related_name "_m2m"
# transitorios de ImagenCultivo (necesarios en 0005 para no chocar con los
# related_name de las FKs viejas mientras ambas coexistían) a los nombres
# finales que usa repository/models.py.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0006_backfill_imagencultivo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='analisis',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='cultivo',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='fecha_procesamiento',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='lote',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='procesada',
        ),
        migrations.RemoveField(
            model_name='imagenrepositorio',
            name='usuario',
        ),
        migrations.AlterField(
            model_name='imagenrepositorio',
            name='repositorio',
            field=models.ForeignKey(blank=True, help_text='Repositorio con el que se descubrió este asset por primera vez (informativo).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imagenes', to='repository.repositorioimagen'),
        ),
        migrations.AlterField(
            model_name='imagencultivo',
            name='analisis',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imagenes', to='metricas.analisis'),
        ),
        migrations.AlterField(
            model_name='imagencultivo',
            name='cultivo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes_repositorio', to='cultivos.cultivo'),
        ),
        migrations.AlterField(
            model_name='imagencultivo',
            name='lote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imagenes_repositorio', to='lotes.lote'),
        ),
        migrations.AlterField(
            model_name='imagencultivo',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes_repositorio', to=settings.AUTH_USER_MODEL),
        ),
    ]
