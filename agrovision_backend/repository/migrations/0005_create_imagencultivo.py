# Paso 1/3 de la migración a relación muchos-a-muchos imagen<->cultivo:
# crea la tabla de asociación. Los campos viejos de ImagenRepositorio
# (cultivo/lote/usuario/estado/procesada/analisis/fecha_procesamiento)
# se mantienen todavía — se copian a esta tabla nueva en la migración de
# datos 0006 antes de eliminarlos en 0007. Nunca se combinan estos tres
# pasos en una sola migración: hacerlo borraría las FKs viejas (y con
# ellas la relación cultivo/usuario de cada imagen ya sincronizada) antes
# de poder copiarlas.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cultivos', '0002_cultivo_latitud_cultivo_longitud'),
        ('lotes', '0002_lote_ancho_lote_largo_lote_latitud_lote_longitud'),
        ('metricas', '0007_alter_analisis_estado'),
        ('repository', '0004_imagenrepositorio_asset_folder_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImagenCultivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('disponible', 'Disponible'), ('procesando', 'Procesando'), ('procesada', 'Procesada'), ('error', 'Error')], default='disponible', max_length=20)),
                ('procesada', models.BooleanField(default=False)),
                ('fecha_procesamiento', models.DateTimeField(blank=True, null=True)),
                ('fecha_asociacion', models.DateTimeField(auto_now_add=True)),
                ('analisis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imagenes_m2m', to='metricas.analisis')),
                ('cultivo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes_repositorio_m2m', to='cultivos.cultivo')),
                ('imagen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asociaciones', to='repository.imagenrepositorio')),
                ('lote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imagenes_repositorio_m2m', to='lotes.lote')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes_repositorio_m2m', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-fecha_asociacion'],
            },
        ),
        migrations.AddConstraint(
            model_name='imagencultivo',
            constraint=models.UniqueConstraint(fields=('imagen', 'cultivo', 'usuario'), name='unica_asociacion_imagen_cultivo_usuario'),
        ),
    ]
