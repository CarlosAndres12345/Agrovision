import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from metricas.models import Analisis
from ubicaciones.models import Ubicacion
from ubicaciones.validation import UbicacionValidationError, validar_ubicacion_payload

from .models import Cultivo

_ESTADO_ANALISIS_API = {
    "pendiente": "PENDIENTE",
    "procesando": "PROCESANDO",
    "procesado": "COMPLETADO",
    "procesado_con_errores": "COMPLETADO_CON_ERRORES",
    "error": "ERROR",
}

# Estados que cuentan como "hay un resultado utilizable" para el resumen de
# métricas del cultivo — un procesamiento con errores parciales igual generó
# frutos/porcentaje/estimación reales sobre las imágenes que sí terminaron.
_ESTADOS_ANALISIS_CON_RESULTADO = ["procesado", "procesado_con_errores"]


def _serialize_analisis_resumen(analisis: Analisis) -> dict:
    return {
        "id": analisis.id,
        "fecha_procesamiento": analisis.created_at.isoformat(),
        "cantidad_frutos": analisis.cantidad_frutos,
        "frutos_maduros": analisis.frutos_maduros,
        "porcentaje_madurez": float(analisis.porcentaje_madurez) if analisis.porcentaje_madurez is not None else None,
        "estimacion_cosecha": float(analisis.estimacion_cosecha) if analisis.estimacion_cosecha is not None else None,
        "estado": _ESTADO_ANALISIS_API.get(analisis.estado, analisis.estado.upper()),
        "lote_id": analisis.lote_id,
        "mensaje_error": analisis.mensaje_error or None,
    }


def _serialize_ubicacion(u: Ubicacion) -> dict:
    return {
        "latitude": str(u.latitude),
        "longitude": str(u.longitude),
        "address": u.address,
        "source": u.source,
        "accuracy_meters": str(u.accuracy_meters) if u.accuracy_meters is not None else None,
        "captured_at": u.captured_at.isoformat(),
    }


def _serialize_cultivo(cultivo: Cultivo, incluir_ubicacion: bool = False) -> dict:
    data = {
        "id": cultivo.id,
        "nombre": cultivo.nombre,
        "tipo_fruto": cultivo.tipo_fruto,
        "ubicacion": cultivo.ubicacion,
        "latitud": str(cultivo.latitud) if cultivo.latitud is not None else None,
        "longitud": str(cultivo.longitud) if cultivo.longitud is not None else None,
        "area_sembrada": str(cultivo.area_sembrada),
        "fecha_siembra": cultivo.fecha_siembra.isoformat(),
        "descripcion": cultivo.descripcion,
        "ultimo_analisis_estado": getattr(cultivo, "ultimo_analisis_estado", None),
    }
    if incluir_ubicacion:
        # Ubicación "del cultivo" = la que no está atada a un lote específico.
        # Como mucho una fila (ver ubicaciones.api_views: upsert por cultivo+lote).
        ubicacion_actual = cultivo.ubicaciones.filter(lote__isnull=True).first()
        data["location"] = _serialize_ubicacion(ubicacion_actual) if ubicacion_actual else None
    return data


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


def _build_cultivo_from_data(cultivo: Cultivo, data: dict):
    required_fields = ["nombre", "tipo_fruto", "ubicacion", "area_sembrada", "fecha_siembra"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return None, _json_error(f"Faltan campos requeridos: {', '.join(missing_fields)}.", status=400)

    try:
        cultivo.nombre = str(data["nombre"]).strip()
        cultivo.tipo_fruto = str(data["tipo_fruto"]).strip()
        cultivo.ubicacion = str(data["ubicacion"]).strip()
        cultivo.area_sembrada = Decimal(str(data["area_sembrada"]))
        cultivo.fecha_siembra = date.fromisoformat(str(data["fecha_siembra"]))
        cultivo.descripcion = str(data.get("descripcion", "")).strip()
    except (ValueError, InvalidOperation):
        return None, _json_error("Revisa el formato de fecha o de los valores numéricos del cultivo.", status=400)

    return cultivo, None


def _guardar_ubicacion_del_cultivo(cultivo: Cultivo, usuario, location_data: dict) -> Ubicacion:
    """
    Valida y guarda (upsert) la ubicación del cultivo (lote=None), y sincroniza
    Cultivo.latitud/longitud para que las vistas que ya leen esos campos
    (ej. el mapa de detalle de cultivo) sigan funcionando sin cambios.
    Lanza UbicacionValidationError si el payload es inválido — el llamador
    debe estar dentro de una transacción para poder revertir el cultivo.
    """
    campos = validar_ubicacion_payload(location_data)
    ubicacion, _creada = Ubicacion.objects.update_or_create(
        cultivo=cultivo,
        lote=None,
        defaults={**campos, "usuario": usuario},
    )
    cultivo.latitud = campos["latitude"]
    cultivo.longitud = campos["longitude"]
    cultivo.save(update_fields=["latitud", "longitud"])
    return ubicacion


@csrf_exempt
def api_lista_cultivos(request):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method == "GET":
        ultimo_estado_sq = (
            Analisis.objects.filter(cultivo=OuterRef("pk")).order_by("-created_at").values("estado")[:1]
        )
        cultivos = (
            Cultivo.objects.select_related("usuario")
            .filter(usuario=usuario)
            .annotate(ultimo_analisis_estado=Subquery(ultimo_estado_sq))
            .order_by("nombre")
        )
        data = [_serialize_cultivo(cultivo) for cultivo in cultivos]
        return JsonResponse({"results": data}, status=200)

    if request.method == "POST":
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        cultivo = Cultivo(usuario=usuario)
        cultivo, error_response = _build_cultivo_from_data(cultivo, data)
        if error_response:
            return error_response

        location_data = data.get("location")
        try:
            with transaction.atomic():
                cultivo.save()
                if location_data:
                    _guardar_ubicacion_del_cultivo(cultivo, usuario, location_data)
        except UbicacionValidationError as exc:
            # La ubicación era inválida: no queda ni el cultivo ni la ubicación
            # (salvo que la ubicación sea opcional y el cliente no la envíe).
            return _json_error(str(exc), status=400)

        return JsonResponse(_serialize_cultivo(cultivo, incluir_ubicacion=True), status=201)

    return _json_error("Método no permitido.", status=405)


@csrf_exempt
def api_detalle_cultivo(request, cultivo_id):
    if not request.user.is_authenticated:
        return _json_error("Autenticación requerida.", status=401)

    cultivo = get_object_or_404(
        Cultivo.objects.select_related("usuario"),
        pk=cultivo_id,
        usuario=request.user,
    )

    if request.method == "GET":
        return JsonResponse(_serialize_cultivo(cultivo, incluir_ubicacion=True), status=200)

    if request.method in {"PUT", "PATCH"}:
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        cultivo, error_response = _build_cultivo_from_data(cultivo, data)
        if error_response:
            return error_response

        location_data = data.get("location")
        try:
            with transaction.atomic():
                cultivo.save()
                if location_data:
                    _guardar_ubicacion_del_cultivo(cultivo, request.user, location_data)
        except UbicacionValidationError as exc:
            return _json_error(str(exc), status=400)

        return JsonResponse(_serialize_cultivo(cultivo, incluir_ubicacion=True), status=200)

    if request.method == "DELETE":
        cultivo.delete()
        return JsonResponse({"deleted": True, "id": cultivo_id}, status=200)

    return _json_error("Método no permitido.", status=405)


def api_metricas_cultivo(request, cultivo_id):
    """
    GET /api/cultivos/<id>/metricas/

    Métricas reales del cultivo, calculadas desde PostgreSQL:
    - ultimo_analisis: el análisis COMPLETADO más reciente (o null si no hay ninguno).
    - resumen: derivado de ese mismo último análisis.
    - historial: los análisis más recientes (incluye errores), más reciente primero.

    Nunca devuelve 0 como sustituto de "no hay datos": si no hay ningún
    análisis completado, ultimo_analisis y resumen quedan en null.
    """
    if not request.user.is_authenticated:
        return _json_error("Autenticación requerida.", status=401)

    cultivo = get_object_or_404(Cultivo, pk=cultivo_id, usuario=request.user)

    analisis_qs = Analisis.objects.filter(cultivo=cultivo).select_related("lote").order_by("-created_at")

    ultimo_completado = analisis_qs.filter(estado__in=_ESTADOS_ANALISIS_CON_RESULTADO).first()
    total_analisis = analisis_qs.count()
    historial = [_serialize_analisis_resumen(a) for a in analisis_qs[:20]]

    if ultimo_completado is None:
        return JsonResponse(
            {"cultivo_id": cultivo.id, "ultimo_analisis": None, "resumen": None, "historial": historial},
            status=200,
        )

    ultimo_data = _serialize_analisis_resumen(ultimo_completado)

    return JsonResponse(
        {
            "cultivo_id": cultivo.id,
            "ultimo_analisis": ultimo_data,
            "resumen": {
                "total_analisis": total_analisis,
                "cantidad_frutos_ultimo": ultimo_data["cantidad_frutos"],
                "frutos_maduros_ultimo": ultimo_data["frutos_maduros"],
                "porcentaje_madurez_ultimo": ultimo_data["porcentaje_madurez"],
                "estimacion_cosecha_ultima": ultimo_data["estimacion_cosecha"],
            },
            "historial": historial,
        },
        status=200,
    )
