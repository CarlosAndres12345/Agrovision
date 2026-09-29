import json
import logging
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from cultivos.models import Cultivo
from lotes.models import Lote

from .inference_service import procesar_imagenes
from .models import Metrica, Analisis
from ml_models.services.service import process_images, ProcesamientoError

logger = logging.getLogger(__name__)

_EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _decimal_o_none(valor):
    """
    Convierte a Decimal vía str() para evitar que el ruido binario de un
    float (ej. 0.072 -> 0.07199999999999999956...) dispare validaciones de
    max_digits al asignarlo a un DecimalField.
    """
    return Decimal(str(valor)) if valor is not None else None


def _archivo_a_base64(archivo) -> str:
    """Convierte un UploadedFile a data URL base64 para preview."""
    import base64
    contenido = archivo.read()
    ext = os.path.splitext(archivo.name)[1].lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".bmp": "image/bmp"
    }.get(ext, "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(contenido).decode('utf-8')}"


def _serialize_metrica(metrica: Metrica) -> dict:
    return {
        "id": metrica.id,
        "tipo_resultado": metrica.tipo_resultado,
        "valor": str(metrica.valor),
        "unidad": metrica.unidad,
        "fecha_registro": metrica.fecha_registro.isoformat(),
        "descripcion": metrica.descripcion,
        "fuente": metrica.fuente,
        "cultivo_id": metrica.cultivo_id,
        "lote_id": metrica.lote_id,
    }


def _serialize_analisis(analisis: Analisis) -> dict:
    return {
        "id": analisis.id,
        "origen": analisis.origen,
        "estado": analisis.estado,
        "imagen_urls": analisis.imagen_urls,
        "cantidad_imagenes": analisis.cantidad_imagenes,
        "cantidad_frutos": analisis.cantidad_frutos,
        "frutos_maduros": analisis.frutos_maduros,
        "porcentaje_madurez": str(analisis.porcentaje_madurez) if analisis.porcentaje_madurez is not None else None,
        "estimacion_cosecha": str(analisis.estimacion_cosecha) if analisis.estimacion_cosecha is not None else None,
        "mensaje_error": analisis.mensaje_error,
        "resultado_json": analisis.resultado_json,
        "notas": analisis.notas,
        "cultivo_id": analisis.cultivo_id,
        "lote_id": analisis.lote_id,
        "created_at": analisis.created_at.isoformat(),
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


# ==================== ANÁLISIS ====================


def _get_authenticated_user(request):
    if not request.user.is_authenticated:
        return None, _json_error("Autenticación requerida.", status=401)
    return request.user, None


def _get_cultivo_usuario(user, cultivo_id):
    return get_object_or_404(Cultivo, pk=cultivo_id, usuario=user)


@csrf_exempt
def api_lista_analisis(request):
    """GET /api/analisis/ - Lista análisis del usuario"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method == "GET":
        analisis = (
            Analisis.objects.filter(usuario=usuario)
            .select_related("cultivo", "lote")
            .order_by("-created_at")
        )
        return JsonResponse({"results": [_serialize_analisis(a) for a in analisis]}, status=200)

    return _json_error("Método no permitido.", status=405)


@csrf_exempt
def api_crear_analisis_manual(request):
    """
    POST /api/analisis/manual/
    Content-Type: multipart/form-data

    Campos:
        cultivo_id  int      requerido
        lote_id     int      opcional
        imagenes    File[]   al menos 1 imagen
        notas       string   opcional (descripción)

    Procesa imágenes con el modelo ML y persiste métricas en tabla Metrica.
    Usa FormData en el frontend para evitar problemas de tamaño con JSON.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    cultivo_id = request.POST.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")

    try:
        cultivo = _get_cultivo_usuario(usuario, cultivo_id)
    except Exception:
        return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

    lote_id = request.POST.get("lote_id") or None
    lote = None
    if lote_id:
        try:
            lote = Lote.objects.get(pk=lote_id, cultivo=cultivo)
        except Lote.DoesNotExist:
            return _json_error("El lote no existe o no pertenece al cultivo.", status=400)

    imagenes = request.FILES.getlist("imagenes")
    if not imagenes:
        return _json_error("Se requiere al menos una imagen en el campo 'imagenes'.")

    # Validar extensiones
    for archivo in imagenes:
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in _EXTENSIONES_VALIDAS:
            return _json_error(
                f"Archivo '{archivo.name}' no válido. "
                f"Solo se aceptan: {', '.join(sorted(_EXTENSIONES_VALIDAS))}."
            )

    # Procesar imágenes con el servicio ML principal
    try:
        service_output = process_images(
            archivos=list(imagenes),
            cultivo_id=int(cultivo_id),
            lote_id=int(lote_id) if lote_id else None,
            notas=str(request.POST.get("notas", "")),
        )
    except ProcesamientoError as e:
        analisis_error = Analisis(
            usuario=usuario, cultivo=cultivo, lote=lote, origen="manual", estado="error",
            cantidad_imagenes=len(imagenes), mensaje_error=str(e),
        )
        analisis_error.save()
        return _json_error(str(e), status=400)
    except Exception as e:
        logger.exception("Error al procesar imágenes (análisis manual, cultivo_id=%s)", cultivo_id)
        analisis_error = Analisis(
            usuario=usuario, cultivo=cultivo, lote=lote, origen="manual", estado="error",
            cantidad_imagenes=len(imagenes), mensaje_error="El procesamiento no pudo completarse.",
        )
        analisis_error.save()
        return _json_error("El procesamiento no pudo completarse.", status=500)

    resultado_json = service_output["resultado_json"]

    # Convertir a base64 para preview (limitado a primeras 4 imágenes)
    import base64
    imagen_urls = []
    archivos_preview = imagenes[:4]
    for archivo in archivos_preview:
        archivo.seek(0)
        try:
            imagen_urls.append(_archivo_a_base64(archivo))
        except Exception:
            imagen_urls.append({"nombre": archivo.name, "url": None})

    # Crear el análisis y sus métricas de forma transaccional: si algo falla
    # a mitad de camino no queda un Analisis sin sus Metrica asociadas.
    tipos_validos = [t[0] for t in Metrica.TIPOS_RESULTADO]
    fecha_ahora = datetime.now()
    metricas_creadas = []

    try:
        with transaction.atomic():
            analisis = Analisis(
                usuario=usuario,
                cultivo=cultivo,
                lote=lote,
                origen="manual",
                estado="procesado",
                imagen_urls=imagen_urls,
                cantidad_imagenes=len(imagenes),
                cantidad_frutos=resultado_json.get("cantidad_frutos", {}).get("valor"),
                frutos_maduros=resultado_json.get("frutos_maduros", {}).get("valor"),
                porcentaje_madurez=_decimal_o_none(resultado_json.get("porcentaje_madurez", {}).get("valor")),
                estimacion_cosecha=_decimal_o_none(resultado_json.get("estimacion_cosecha", {}).get("valor")),
                notas=service_output.get("notas", ""),
                resultado_json=resultado_json,
            )
            analisis.full_clean()
            analisis.save()

            for tipo, datos in resultado_json.items():
                if tipo not in tipos_validos:
                    continue
                metrica = Metrica(
                    cultivo=cultivo,
                    lote=lote,
                    tipo_resultado=tipo,
                    valor=Decimal(str(datos["valor"])),
                    unidad=datos["unidad"],
                    fecha_registro=fecha_ahora,
                    descripcion=(
                        f"Procesado por modelo de visión ({service_output['imagenes_procesadas']} imagen"
                        f"{'es' if service_output['imagenes_procesadas'] != 1 else ''})."
                    ),
                    fuente="modelo_vision",
                )
                metrica.save()
                metricas_creadas.append(_serialize_metrica(metrica))
    except ValidationError as e:
        return _json_error("; ".join(e.messages), status=400)

    # Generar imagen anotada con bounding boxes sobre el mismo canvas que vio
    # el modelo (redimensionado) — los boxes vienen normalizados a ese canvas.
    imagen_anotada_url = None
    try:
        from PIL import Image, ImageDraw
        from pathlib import Path
        from ml_models.utils.image_utils import leer_desde_bytes, redimensionar

        primera = imagenes[0]
        primera.seek(0)
        arr = redimensionar(leer_desde_bytes(primera.read()))
        primera.seek(0)
        img = Image.fromarray(arr)
        draw = ImageDraw.Draw(img)
        w, h = img.size

        boxes_filtrados = resultado_json.get("debug", {}).get("boxes_filtrados", [])
        scores_filtrados = resultado_json.get("debug", {}).get("scores_filtrados", [])

        for idx, box in enumerate(boxes_filtrados):
            x1, y1, x2, y2 = box
            left = x1 * w
            top = y1 * h
            right = x2 * w
            bottom = y2 * h
            draw.rectangle([left, top, right, bottom], outline="lime", width=3)
            score = scores_filtrados[idx] if idx < len(scores_filtrados) else None
            label = f"{score:.2f}" if score is not None else ""
            if label:
                draw.text((left, max(0, top - 14)), label, fill="lime")

        media_dir = Path(settings.MEDIA_ROOT) / "analisis"
        media_dir.mkdir(parents=True, exist_ok=True)
        nombre_archivo = f"analisis_{analisis.id}_anotada.jpg"
        ruta_guardado = media_dir / nombre_archivo
        img.save(ruta_guardado, "JPEG", quality=90)
        imagen_anotada_url = f"{settings.MEDIA_URL}analisis/{nombre_archivo}"
    except Exception:
        imagen_anotada_url = None

    return JsonResponse({
        "analisis": _serialize_analisis(analisis),
        "metricas": metricas_creadas,
        "modelo_usado": service_output.get("modelo_usado", "unknown"),
        "imagenes_procesadas": service_output["imagenes_procesadas"],
        "debug": resultado_json.get("debug", {}),
        "imagen_anotada_url": imagen_anotada_url,
    }, status=201)


@csrf_exempt
def api_detalle_analisis(request, analisis_id):
    """GET/PUT/DELETE /api/analisis/<id>/"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    analisis = get_object_or_404(
        Analisis.objects.select_related("cultivo", "lote"),
        pk=analisis_id,
        usuario=usuario,
    )

    if request.method == "GET":
        return JsonResponse(_serialize_analisis(analisis), status=200)

    if request.method in {"PUT", "PATCH"}:
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        analisis.notas = str(data.get("notas", "")).strip()
        if "estado" in data:
            estados_validos = [e[0] for e in Analisis.ESTADO_CHOICES]
            if data["estado"] in estados_validos:
                analisis.estado = data["estado"]

        analisis.save()
        return JsonResponse(_serialize_analisis(analisis), status=200)

    if request.method == "DELETE":
        analisis.delete()
        return JsonResponse({"deleted": True, "id": analisis_id}, status=200)

    return _json_error("Método no permitido.", status=405)


def api_ultimo_analisis_lote(request, lote_id):
    """GET /api/analisis/lote/<lote_id>/ultimo/ - Último análisis de un lote"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method != "GET":
        return _json_error("Método no permitido.", status=405)

    try:
        lote = Lote.objects.select_related("cultivo").get(pk=lote_id)
        if lote.cultivo.usuario != usuario:
            return _json_error("No tienes acceso a este lote.", status=403)
    except Lote.DoesNotExist:
        return _json_error("Lote no encontrado.", status=404)

    ultimo = (
        Analisis.objects.filter(usuario=usuario, lote_id=lote_id)
        .select_related("cultivo", "lote")
        .order_by("-created_at")
        .first()
    )

    if not ultimo:
        return JsonResponse({"results": None}, status=200)

    return JsonResponse({"results": _serialize_analisis(ultimo)}, status=200)


def api_ultimo_analisis_cultivo(request, cultivo_id):
    """GET /api/analisis/cultivo/<cultivo_id>/ultimo/ - Último análisis de un cultivo"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method != "GET":
        return _json_error("Método no permitido.", status=405)

    try:
        cultivo = Cultivo.objects.get(pk=cultivo_id, usuario=usuario)
    except Cultivo.DoesNotExist:
        return _json_error("Cultivo no encontrado.", status=404)

    ultimo = (
        Analisis.objects.filter(usuario=usuario, cultivo_id=cultivo_id)
        .select_related("cultivo", "lote")
        .order_by("-created_at")
        .first()
    )

    if not ultimo:
        return JsonResponse({"results": None}, status=200)

    return JsonResponse({"results": _serialize_analisis(ultimo)}, status=200)


# ==================== MÉTRICAS (existente) ====================


@csrf_exempt
def api_crear_metrica(request):
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    data, error_response = _parse_json_body(request)
    if error_response:
        return error_response

    # Cultivo requerido
    cultivo_id = data.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")
    try:
        cultivo = Cultivo.objects.get(pk=cultivo_id)
    except Cultivo.DoesNotExist:
        return _json_error("El cultivo seleccionado no existe.", status=404)

    # tipo_resultado: solo los 4 valores oficiales
    tipos_validos = [t[0] for t in Metrica.TIPOS_RESULTADO]
    tipo = str(data.get("tipo_resultado", "")).strip()
    if tipo not in tipos_validos:
        return _json_error(
            f"tipo_resultado debe ser uno de: {', '.join(tipos_validos)}."
        )

    # valor numérico
    try:
        valor = Decimal(str(data.get("valor", "")))
    except (InvalidOperation, ValueError):
        return _json_error("valor debe ser un número válido.")

    # fecha_registro en ISO 8601
    fecha_str = str(data.get("fecha_registro", "")).strip()
    if not fecha_str:
        return _json_error("fecha_registro es requerida.")
    try:
        fecha = datetime.fromisoformat(fecha_str)
    except ValueError:
        return _json_error(
            "fecha_registro debe tener formato ISO 8601 (YYYY-MM-DDTHH:MM:SS)."
        )

    # lote opcional — si se provee, debe pertenecer al cultivo
    lote_id = data.get("lote_id")
    lote = None
    if lote_id:
        try:
            lote = Lote.objects.get(pk=lote_id, cultivo=cultivo)
        except Lote.DoesNotExist:
            return _json_error(
                "El lote no existe o no pertenece al cultivo seleccionado.",
                status=400,
            )

    fuente = str(data.get("fuente", "registro_manual")).strip() or "registro_manual"

    metrica = Metrica(
        cultivo=cultivo,
        lote=lote,
        tipo_resultado=tipo,
        valor=valor,
        unidad=str(data.get("unidad", "")).strip(),
        fecha_registro=fecha,
        descripcion=str(data.get("descripcion", "")).strip(),
        fuente=fuente,
    )
    metrica.save()

    return JsonResponse(_serialize_metrica(metrica), status=201)


@csrf_exempt
def api_procesar_dataset(request):
    """
    POST /api/metricas/procesar/
    Content-Type: multipart/form-data

    Campos:
        cultivo_id  int      requerido
        lote_id     int      opcional
        imagenes    File[]   al menos 1 imagen

    Invoca el pipeline de inferencia y persiste las 4 métricas oficiales.
    """
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    cultivo_id = request.POST.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")
    try:
        cultivo = Cultivo.objects.get(pk=cultivo_id)
    except Cultivo.DoesNotExist:
        return _json_error("El cultivo seleccionado no existe.", status=404)

    lote_id = request.POST.get("lote_id") or None
    lote = None
    if lote_id:
        try:
            lote = Lote.objects.get(pk=lote_id, cultivo=cultivo)
        except Lote.DoesNotExist:
            return _json_error(
                "El lote no existe o no pertenece al cultivo seleccionado.",
                status=400,
            )

    imagenes = request.FILES.getlist("imagenes")
    if not imagenes:
        return _json_error("Se requiere al menos una imagen en el campo 'imagenes'.")

    for archivo in imagenes:
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in _EXTENSIONES_VALIDAS:
            return _json_error(
                f"Archivo '{archivo.name}' no válido. "
                f"Solo se aceptan imágenes: {', '.join(sorted(_EXTENSIONES_VALIDAS))}."
            )

    resultados = procesar_imagenes(imagenes)

    fecha_ahora = datetime.now()
    metricas_creadas = []
    tipos_validos = [t[0] for t in Metrica.TIPOS_RESULTADO]

    for tipo, datos in resultados.items():
        if tipo not in tipos_validos:
            continue
        metrica = Metrica(
            cultivo=cultivo,
            lote=lote,
            tipo_resultado=tipo,
            valor=Decimal(str(datos["valor"])),
            unidad=datos["unidad"],
            fecha_registro=fecha_ahora,
            descripcion=(
                f"Procesado por modelo de visión a partir de "
                f"{len(imagenes)} imagen{'es' if len(imagenes) != 1 else ''}."
            ),
            fuente="modelo_vision",
        )
        metrica.save()
        metricas_creadas.append(_serialize_metrica(metrica))

    return JsonResponse(
        {
            "cultivo_id": cultivo.id,
            "lote_id": lote.id if lote else None,
            "imagenes_procesadas": len(imagenes),
            "metricas": metricas_creadas,
        },
        status=201,
    )


def api_metricas_por_cultivo(request, cultivo_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    cultivo = get_object_or_404(Cultivo, pk=cultivo_id, usuario=usuario)
    metricas = cultivo.metricas.select_related("lote").order_by("-fecha_registro", "-created_at")
    data = [_serialize_metrica(metrica) for metrica in metricas]
    return JsonResponse({"cultivo_id": cultivo.id, "results": data}, status=200)


def api_resumen_metricas_por_cultivo(request, cultivo_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    cultivo = get_object_or_404(Cultivo, pk=cultivo_id, usuario=usuario)
    metricas = cultivo.metricas.order_by("-fecha_registro", "-created_at")

    resumen = {
        "cantidad_frutos": None,
        "frutos_maduros": None,
        "estimacion_cosecha": None,
        "porcentaje_madurez": None,
    }

    for metrica in metricas:
        if metrica.tipo_resultado in resumen and resumen[metrica.tipo_resultado] is None:
            resumen[metrica.tipo_resultado] = {
                "valor": str(metrica.valor),
                "unidad": metrica.unidad,
                "fecha_registro": metrica.fecha_registro.isoformat(),
            }

    return JsonResponse(
        {
            "cultivo_id": cultivo.id,
            "metricas": resumen,
        },
        status=200,
    )


def api_metricas_por_lote(request, lote_id):
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    lote = get_object_or_404(Lote.objects.select_related("cultivo"), pk=lote_id, cultivo__usuario=usuario)
    metricas = (
        Metrica.objects.filter(lote_id=lote.id)
        .order_by("-fecha_registro", "-created_at")
        .select_related("cultivo", "lote")
    )

    def _serialize_for_lote(m: Metrica) -> dict:
        try:
            valor = float(m.valor)
        except Exception:
            valor = str(m.valor)

        return {
            "id": m.id,
            "tipo_resultado": m.tipo_resultado,
            "valor": valor,
            "unidad": m.unidad,
            "fecha_registro": m.fecha_registro.isoformat(),
            "fuente": m.fuente,
            "descripcion": m.descripcion,
        }

    data = [_serialize_for_lote(m) for m in metricas]
    return JsonResponse(data, safe=False, status=200)