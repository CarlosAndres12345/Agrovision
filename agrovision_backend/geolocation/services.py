"""
Cliente de geocodificación — hoy implementado sobre Nominatim/OpenStreetMap.

Reglas de uso de Nominatim que este módulo hace cumplir:
- máximo 1 solicitud por segundo, para toda la aplicación (throttle global);
- caché por consulta (evita repetir la misma solicitud a la API externa);
- User-Agent propio que identifica la aplicación;
- timeout explícito y errores traducidos a GeocodingServiceError.

El proveedor (base URL) vive en settings.NOMINATIM_BASE_URL, así que puede
cambiarse sin tocar código — ver TAREA: "permitir cambiar posteriormente el
proveedor mediante configuración".
"""

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

MIN_SECONDS_BETWEEN_REQUESTS = 1.0
REQUEST_TIMEOUT_SECONDS = 5
CACHE_TTL_SECONDS = 60 * 60  # 1 hora
CACHE_PREFIX = "geolocation"

_throttle_lock = threading.Lock()
_last_request_at = 0.0


class GeocodingServiceError(Exception):
    """Error al comunicarse con el proveedor de geocodificación."""


def _throttle() -> None:
    """
    Garantiza como mínimo MIN_SECONDS_BETWEEN_REQUESTS entre solicitudes
    salientes al proveedor, sin importar cuántas peticiones concurrentes
    lleguen a nuestro backend (lock global del proceso).
    """
    global _last_request_at
    with _throttle_lock:
        ahora = time.monotonic()
        espera = MIN_SECONDS_BETWEEN_REQUESTS - (ahora - _last_request_at)
        if espera > 0:
            time.sleep(espera)
        _last_request_at = time.monotonic()


def _user_agent() -> str:
    return getattr(
        settings, "NOMINATIM_USER_AGENT", "AgriVisionOS/1.0 (contacto no configurado)"
    )


def _base_url() -> str:
    return getattr(settings, "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")


def _get_json(path: str, params: dict) -> object:
    url = f"{_base_url()}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": _user_agent()})

    _throttle()
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise GeocodingServiceError(f"El proveedor de geocodificación respondió {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GeocodingServiceError(f"No se pudo contactar al proveedor de geocodificación: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise GeocodingServiceError("Respuesta inválida del proveedor de geocodificación.") from exc


def buscar_direccion(query: str, limit: int = 5) -> list[dict]:
    """
    GET /search — busca lugares que coincidan con `query`.
    Devuelve como máximo `limit` resultados: [{lat, lon, display_name, address}].
    """
    cache_key = f"{CACHE_PREFIX}:search:{query.strip().lower()}:{limit}"
    cacheado = cache.get(cache_key)
    if cacheado is not None:
        return cacheado

    data = _get_json(
        "/search",
        {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
            "countrycodes": "co",
        },
    )
    if not isinstance(data, list):
        raise GeocodingServiceError("Respuesta inesperada del proveedor de geocodificación.")

    resultados = [
        {
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
            "display_name": item.get("display_name", ""),
            "address": item.get("address", {}),
        }
        for item in data
        if "lat" in item and "lon" in item
    ]

    cache.set(cache_key, resultados, CACHE_TTL_SECONDS)
    return resultados


def geocodificar_inverso(lat: float, lon: float) -> dict | None:
    """
    GET /reverse — dirección aproximada para un punto.
    Redondea a 5 decimales (~1 m) para aprovechar la caché en clics cercanos.
    """
    lat_r, lon_r = round(lat, 5), round(lon, 5)
    cache_key = f"{CACHE_PREFIX}:reverse:{lat_r}:{lon_r}"
    cacheado = cache.get(cache_key)
    if cacheado is not None:
        return cacheado

    data = _get_json(
        "/reverse",
        {"lat": lat_r, "lon": lon_r, "format": "jsonv2", "addressdetails": 1, "zoom": 18},
    )
    if not isinstance(data, dict) or "display_name" not in data:
        resultado = None
    else:
        resultado = {"display_name": data.get("display_name", ""), "address": data.get("address", {})}

    cache.set(cache_key, resultado, CACHE_TTL_SECONDS)
    return resultado
