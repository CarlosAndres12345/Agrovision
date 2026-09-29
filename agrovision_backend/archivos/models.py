from pathlib import Path

from django.db import models  # noqa: F401 — requerido por migraciones históricas


def ruta_imagen_cultivo(instance, filename):
    """
    Mantenida solo porque migraciones históricas (0003) la referencian
    directamente como `upload_to`. El modelo ImagenCultivo ya no existe
    (repositorio reemplazado por Cloudinary, ver app 'repository').
    """
    extension = Path(filename).suffix.lower()
    return f"cultivos/{instance.cultivo_id}/{extension}"
