# Generated migration for Analisis model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cultivos', '0002_cultivo_latitud_cultivo_longitud'),
        ('lotes', '0002_lote_ancho_lote_largo_lote_latitud_lote_longitud'),
        ('metricas', '0002_alter_metrica_tipo_resultado'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Analisis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origen', models.CharField(choices=[('manual', 'Subida manual'), ('drive_url', 'URL de Drive')], max_length=20)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('procesado', 'Procesado'), ('error', 'Error')], default='pendiente', max_length=20)),
                ('imagen_urls', models.JSONField(blank=True, default=list)),
                ('drive_url', models.URLField(blank=True, max_length=500)),
                ('resultado_json', models.JSONField(blank=True, default=dict)),
                ('notas', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cultivo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analisis', to='cultivos.cultivo')),
                ('lote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analisis', to='lotes.lote')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analisis', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]