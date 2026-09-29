import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from cultivos.models import Cultivo
from lotes.models import Lote

from .models import Ubicacion
from .validation import UbicacionValidationError, validar_ubicacion_payload


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"detail": message}, status=status)


def _parse_json_body(request):
    try:
        raw = request.body.decode("utf-8") if request.body else "{}"
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, _json_error("JSON inválido en la petición.", status=400)

    if not isinstance(data, dict):
        return None, _json_error("Se esperaba un objeto JSON.", status=400)

    return data, None


def _get_authenticated_user(request):
    if not request.user.is_authenticated:
        return None, _json_error("Autenticación requerida.", status=401)
    return request.user, None


def _serialize(u: Ubicacion) -> dict:
    return {
        "id": u.id,
        "cultivo_id": u.cultivo_id,
        "lote_id": u.lote_id,
        "latitude": str(u.latitude),
        "longitude": str(u.longitude),
        "address": u.address,
        "accuracy_meters": str(u.accuracy_meters) if u.accuracy_meters is not None else None,
        "captured_at": u.captured_at.isoformat(),
        "source": u.source,
        "created_at": u.created_at.isoformat(),
    }


@csrf_exempt
def api_crear_ubicacion(request):
    """
    POST /api/ubicaciones/
    {
        "cultivo_id": 1,
        "lote_id": 1 (opcional),
        "latitude": 3.4516,
        "longitude": -76.5320,
        "address": "Dirección o descripción encontrada" (opcional),
        "source": "DEVICE_GEOLOCATION" | "ADDRESS_SEARCH" | "MAP_SELECTION",
        "accuracy_meters": 12.4 (opcional — solo tiene sentido para DEVICE_GEOLOCATION),
        "captured_at": "2026-08-05T10:00:00.000Z" (opcional, por defecto ahora)
    }

    Semántica de upsert: como mucho una Ubicacion por (cultivo, lote) — una
    nueva confirmación reemplaza a la anterior en vez de acumular historial,
    para no crear registros duplicados para el mismo cultivo.

    No confía en los datos del cliente más allá de format/rango: valida
    latitud/longitud, que `source` sea uno de los 3 valores permitidos, que
    el lote (si se envía) pertenezca al cultivo, y que el usuario esté
    autenticado y sea dueño del cultivo.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    data, error_response = _parse_json_body(request)
    if error_response:
        return error_response

    cultivo_id = data.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")
    cultivo = Cultivo.objects.filter(pk=cultivo_id, usuario=usuario).first()
    if cultivo is None:
        return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

    lote_id = data.get("lote_id")
    lote = None
    if lote_id:
        try:
            lote = Lote.objects.get(pk=lote_id, cultivo=cultivo)
        except Lote.DoesNotExist:
            return _json_error("El lote no existe o no pertenece al cultivo indicado.", status=400)

    try:
        campos = validar_ubicacion_payload(data)
    except UbicacionValidationError as exc:
        return _json_error(str(exc))

    ubicacion, _creada = Ubicacion.objects.update_or_create(
        cultivo=cultivo,
        lote=lote,
        defaults={**campos, "usuario": usuario},
    )

    return JsonResponse(_serialize(ubicacion), status=201)


def api_ubicaciones_por_cultivo(request, cultivo_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    cultivo = get_object_or_404(Cultivo, pk=cultivo_id, usuario=usuario)
    ubicaciones = cultivo.ubicaciones.select_related("lote").order_by("-captured_at")
    return JsonResponse(
        {"cultivo_id": cultivo.id, "results": [_serialize(u) for u in ubicaciones]},
        status=200,
    )


def api_ubicaciones_por_lote(request, lote_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    lote = get_object_or_404(Lote.objects.select_related("cultivo"), pk=lote_id, cultivo__usuario=usuario)
    ubicaciones = (
        Ubicacion.objects
        .filter(lote_id=lote.id)
        .order_by("-captured_at")
        .select_related("cultivo", "lote")
    )
    return JsonResponse(
        {"lote_id": lote.id, "results": [_serialize(u) for u in ubicaciones]},
        status=200,
    )
