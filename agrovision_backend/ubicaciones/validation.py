"""
Validación de un payload de ubicación, compartida entre:
- ubicaciones/api_views.py (POST /api/ubicaciones/ standalone);
- cultivos/api_views.py (ubicación anidada al crear/editar un cultivo).

Evita duplicar las mismas reglas en dos sitios.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import Ubicacion

ADDRESS_MAX_LENGTH = 500
SOURCES_VALIDOS = [c[0] for c in Ubicacion.SOURCE_CHOICES]


class UbicacionValidationError(Exception):
    """Payload de ubicación inválido — mensaje ya listo para mostrar al usuario."""


def validar_ubicacion_payload(data: dict) -> dict:
    """
    Valida {latitude, longitude, address, source, accuracy_meters, captured_at}
    y devuelve un dict listo para crear/actualizar un Ubicacion (sin cultivo,
    lote ni usuario — eso lo agrega quien llama, tras verificar pertenencia).
    """
    source = str(data.get("source", "")).strip()
    if source not in SOURCES_VALIDOS:
        raise UbicacionValidationError(f"source debe ser uno de: {', '.join(SOURCES_VALIDOS)}.")

    try:
        latitude = Decimal(str(data.get("latitude")))
        longitude = Decimal(str(data.get("longitude")))
    except (InvalidOperation, TypeError):
        raise UbicacionValidationError("latitude y longitude deben ser numéricos.")

    if not (-90 <= latitude <= 90):
        raise UbicacionValidationError("La latitud debe estar entre -90 y 90.")
    if not (-180 <= longitude <= 180):
        raise UbicacionValidationError("La longitud debe estar entre -180 y 180.")

    accuracy_raw = data.get("accuracy_meters")
    accuracy_meters = None
    if accuracy_raw not in (None, ""):
        try:
            accuracy_meters = Decimal(str(accuracy_raw))
        except InvalidOperation:
            raise UbicacionValidationError("accuracy_meters debe ser numérico.")
        if accuracy_meters < 0:
            raise UbicacionValidationError("accuracy_meters debe ser mayor o igual a 0.")

    if source == Ubicacion.DEVICE_GEOLOCATION and accuracy_meters is None:
        raise UbicacionValidationError("accuracy_meters es requerido cuando source es DEVICE_GEOLOCATION.")

    address = str(data.get("address", "")).strip()
    if len(address) > ADDRESS_MAX_LENGTH:
        raise UbicacionValidationError(f"address no puede superar los {ADDRESS_MAX_LENGTH} caracteres.")

    captured_at_raw = str(data.get("captured_at", "")).strip()
    if captured_at_raw:
        try:
            captured_at = datetime.fromisoformat(captured_at_raw.replace("Z", "+00:00"))
        except ValueError:
            raise UbicacionValidationError("captured_at debe tener formato ISO 8601.")
    else:
        captured_at = datetime.now()

    return {
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "source": source,
        "accuracy_meters": accuracy_meters,
        "captured_at": captured_at,
    }
