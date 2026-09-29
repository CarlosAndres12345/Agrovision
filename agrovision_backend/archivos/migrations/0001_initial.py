import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cultivos', '0001_initial'),
        ('lotes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivoDrive',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('drive_folder_id', models.CharField(blank=True, max_length=200)),
                ('drive_folder_url', models.URLField(blank=True, max_length=500)),
                ('drive_files', models.JSONField(default=list)),
                ('cantidad_archivos', models.IntegerField(default=0)),
                ('notas', models.TextField(blank=True)),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                (
                    'cultivo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='archivos_drive',
                        to='cultivos.cultivo',
                    ),
                ),
                (
                    'lote',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='archivos_drive',
                        to='lotes.lote',
                    ),
                ),
            ],
            options={
                'ordering': ['-fecha_subida'],
            },
        ),
    ]
