import archivos.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cultivos', '0002_cultivo_latitud_cultivo_longitud'),
        ('lotes', '0002_lote_ancho_lote_largo_lote_latitud_lote_longitud'),
        ('archivos', '0002_driveconfiguracion_alter_archivodrive_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ArchivoDrive',
        ),
        migrations.DeleteModel(
            name='DriveConfiguracion',
        ),
        migrations.CreateModel(
            name='ImagenCultivo',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('imagen', models.ImageField(upload_to=archivos.models.ruta_imagen_cultivo)),
                ('nombre_original', models.CharField(blank=True, max_length=255)),
                ('notas', models.TextField(blank=True)),
                ('subida_en', models.DateTimeField(auto_now_add=True)),
                (
                    'cultivo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='imagenes',
                        to='cultivos.cultivo',
                    ),
                ),
                (
                    'lote',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='imagenes',
                        to='lotes.lote',
                    ),
                ),
            ],
            options={
                'ordering': ['-subida_en'],
            },
        ),
    ]
