# Paso 2/3: copia cada asociación imagen<->cultivo que hoy vive como FK
# directa en ImagenRepositorio hacia la tabla ImagenCultivo, antes de que
# el paso 3 (0007) elimine esas FKs. Usa los modelos históricos (`apps`),
# no los de repository/models.py, porque en este punto de la historia de
# migraciones ImagenRepositorio TODAVÍA tiene cultivo/lote/usuario/estado/
# procesada/analisis/fecha_procesamiento.

from django.db import migrations


def copiar_asociaciones(apps, schema_editor):
    ImagenRepositorio = apps.get_model('repository', 'ImagenRepositorio')
    ImagenCultivo = apps.get_model('repository', 'ImagenCultivo')

    creadas = 0
    for imagen in ImagenRepositorio.objects.filter(cultivo_id__isnull=False).iterator():
        ImagenCultivo.objects.create(
            imagen_id=imagen.id,
            cultivo_id=imagen.cultivo_id,
            lote_id=imagen.lote_id,
            usuario_id=imagen.usuario_id,
            estado=imagen.estado,
            procesada=imagen.procesada,
            analisis_id=imagen.analisis_id,
            fecha_procesamiento=imagen.fecha_procesamiento,
            fecha_asociacion=imagen.fecha_sincronizacion,
        )
        creadas += 1

    print(f"[0006_backfill_imagencultivo] {creadas} asociación(es) creada(s) desde ImagenRepositorio existentes.")


def revertir(apps, schema_editor):
    # Reversa: borra todo lo que haya creado esta migración de datos. Segura
    # de aplicar sola porque en el momento de revertir, ImagenRepositorio
    # todavía conserva sus FKs viejas (0007 se revierte primero).
    ImagenCultivo = apps.get_model('repository', 'ImagenCultivo')
    ImagenCultivo.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0005_create_imagencultivo'),
    ]

    operations = [
        migrations.RunPython(copiar_asociaciones, revertir),
    ]
