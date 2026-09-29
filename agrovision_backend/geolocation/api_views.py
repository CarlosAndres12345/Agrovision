from django.http import JsonResponse

from . import services

MIN_QUERY_LENGTH = 3


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"detail": message}, status=status)


def _get_authenticated_user(request):
    if not request.user.is_authenticated:
        return None, _json_error("Autenticación requerida.", status=401)
    return request.user, None


def api_geolocation_search(request):
    """
    GET /api/geolocation/search/?q=<direccion>

    Proxy cacheado y limitado a Nominatim — el frontend nunca llama a
    Nominatim directamente. Nunca reenvía datos personales: solo el texto
    de búsqueda que el propio usuario escribió.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "GET":
        return _json_error("Método no permitido.", status=405)

    query = str(request.GET.get("q", "")).strip()
    if len(query) < MIN_QUERY_LENGTH:
        return _json_error(f"q debe tener al menos {MIN_QUERY_LENGTH} caracteres.")

    try:
        resultados = services.buscar_direccion(query)
    except services.GeocodingServiceError as exc:
        return _json_error(str(exc), status=502)

    return JsonResponse({"results": resultados}, status=200)


def api_geolocation_reverse(request):
    """
    GET /api/geolocation/reverse/?lat=<lat>&lon=<lon>

    La dirección devuelta es aproximada (proviene de Nominatim) — no se
    garantiza que coincida exactamente con el punto seleccionado.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "GET":
        return _json_error("Método no permitido.", status=405)

    try:
        lat = float(request.GET.get("lat"))
        lon = float(request.GET.get("lon"))
    except (TypeError, ValueError):
        return _json_error("lat y lon son requeridos y deben ser numéricos.")

    if not (-90 <= lat <= 90):
        return _json_error("lat debe estar entre -90 y 90.")
    if not (-180 <= lon <= 180):
        return _json_error("lon debe estar entre -180 y 180.")

    try:
        resultado = services.geocodificar_inverso(lat, lon)
    except services.GeocodingServiceError as exc:
        return _json_error(str(exc), status=502)

    return JsonResponse({"result": resultado}, status=200)
