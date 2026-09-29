# Generated migration for adding latitud and longitud to Cultivo

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cultivos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cultivo',
            name='latitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='cultivo',
            name='longitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
    ]