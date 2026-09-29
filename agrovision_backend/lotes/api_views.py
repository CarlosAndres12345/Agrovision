import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from cultivos.models import Cultivo

from .models import Lote


def _get_authenticated_user(request):
    if not request.user.is_authenticated:
        return None, _json_error("Autenticación requerida.", status=401)
    return request.user, None


def _get_owned_cultivo(user, cultivo_id):
    return get_object_or_404(Cultivo, pk=cultivo_id, usuario=user)


def _get_owned_lote(user, lote_id):
    return get_object_or_404(Lote.objects.select_related("cultivo"), pk=lote_id, cultivo__usuario=user)


def _serialize_lote(lote: Lote) -> dict:
    return {
        "id": lote.id,
        "nombre": lote.nombre,
        "ancho": str(lote.ancho) if lote.ancho is not None else None,
        "largo": str(lote.largo) if lote.largo is not None else None,
        "area_lote": str(lote.area_lote),
        "latitud": str(lote.latitud) if lote.latitud is not None else None,
        "longitud": str(lote.longitud) if lote.longitud is not None else None,
        "descripcion": lote.descripcion,
        "cultivo_id": lote.cultivo_id,
    }


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


def _build_lote_from_data(lote: Lote, data: dict):
    required_fields = ["cultivo_id", "nombre"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return None, _json_error(f"Faltan campos requeridos: {', '.join(missing_fields)}.", status=400)

    try:
        usuario = data.pop("_usuario", None)
        if usuario is None:
            return None, _json_error("Autenticación requerida.", status=401)

        cultivo = Cultivo.objects.filter(pk=data["cultivo_id"], usuario=usuario).first()
        if cultivo is None:
            return None, _json_error("El cultivo seleccionado no existe o no pertenece al usuario autenticado.", status=404)

        lote.cultivo = cultivo
        lote.nombre = str(data["nombre"]).strip()
        lote.descripcion = str(data.get("descripcion", "")).strip()

        ancho_raw = data.get("ancho")
        largo_raw = data.get("largo")
        latitud_raw = data.get("latitud")
        longitud_raw = data.get("longitud")
        area_raw = data.get("area_lote")

        ancho = Decimal(str(ancho_raw)) if ancho_raw not in (None, "") else None
        largo = Decimal(str(largo_raw)) if largo_raw not in (None, "") else None
        latitud = Decimal(str(latitud_raw)) if latitud_raw not in (None, "") else None
        longitud = Decimal(str(longitud_raw)) if longitud_raw not in (None, "") else None

        if (ancho is None) ^ (largo is None):
            return None, _json_error("Debes indicar ancho y largo juntos, o dejar ambos vacíos.", status=400)

        if ancho is not None and ancho <= 0:
            return None, _json_error("El ancho debe ser mayor que cero.", status=400)
        if largo is not None and largo <= 0:
            return None, _json_error("El largo debe ser mayor que cero.", status=400)
        if latitud is not None and not (-90 <= latitud <= 90):
            return None, _json_error("La latitud debe estar entre -90 y 90.", status=400)
        if longitud is not None and not (-180 <= longitud <= 180):
            return None, _json_error("La longitud debe estar entre -180 y 180.", status=400)

        lote.ancho = ancho
        lote.largo = largo
        lote.latitud = latitud
        lote.longitud = longitud

        if ancho is not None and largo is not None:
            lote.area_lote = (ancho * largo).quantize(Decimal("0.01"))
        else:
            if area_raw in (None, ""):
                return None, _json_error("Debes enviar area_lote o las dimensiones ancho y largo.", status=400)
            lote.area_lote = Decimal(str(area_raw))
    except (ValueError, InvalidOperation):
        return None, _json_error("Revisa el formato numérico del lote.", status=400)

    return lote, None


@csrf_exempt
def api_lista_lotes(request):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method == "GET":
        lotes = (
            Lote.objects.select_related("cultivo")
            .filter(cultivo__usuario=usuario)
            .order_by("nombre")
        )
        data = [_serialize_lote(lote) for lote in lotes]
        return JsonResponse({"results": data}, status=200)

    if request.method == "POST":
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        data["_usuario"] = usuario

        lote, error_response = _build_lote_from_data(Lote(), data)
        if error_response:
            return error_response

        lote.save()
        return JsonResponse(_serialize_lote(lote), status=201)

    return _json_error("Método no permitido.", status=405)


@csrf_exempt
def api_detalle_lote(request, lote_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    lote = _get_owned_lote(usuario, lote_id)

    if request.method == "GET":
        return JsonResponse(_serialize_lote(lote), status=200)

    if request.method in {"PUT", "PATCH"}:
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        data["_usuario"] = usuario

        lote, error_response = _build_lote_from_data(lote, data)
        if error_response:
            return error_response

        lote.save()
        return JsonResponse(_serialize_lote(lote), status=200)

    if request.method == "DELETE":
        lote.delete()
        return JsonResponse({"deleted": True, "id": lote_id}, status=200)

    return _json_error("Método no permitido.", status=405)


def api_lotes_por_cultivo(request, cultivo_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    cultivo = _get_owned_cultivo(usuario, cultivo_id)
    lotes = cultivo.lotes.all().order_by("nombre")
    data = [_serialize_lote(lote) for lote in lotes]
    return JsonResponse({"cultivo_id": cultivo.id, "results": data}, status=200)
