import datetime
import io
import json
import logging
import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from cultivos.models import Cultivo
from lotes.models import Lote
from metricas.models import Analisis, Metrica
from ml_models.services.service import process_images, ProcesamientoError

from . import services
from .encryption import SecretDecryptionError
from .models import ImagenCultivo, ImagenRepositorio, RepositorioImagen
from .providers import CloudinaryProvider, RepositoryProviderError, get_provider_for_user

logger = logging.getLogger(__name__)


def _parse_fecha_cloudinary(valor):
    """Convierte el created_at (ISO 8601, ej. '2024-01-01T12:00:00Z') que devuelve Cloudinary a datetime aware."""
    if not valor:
        return None
    dt = parse_datetime(valor)
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, datetime.timezone.utc)
    return dt


def _decimal_o_none(valor):
    """
    Convierte a Decimal vía str() para evitar que el ruido binario de un
    float dispare validaciones de max_digits al asignarlo a un DecimalField.
    """
    return Decimal(str(valor)) if valor is not None else None


class _MemoryImageFile(io.BytesIO):
    """Archivo en memoria compatible con process_images (name/read/seek). No toca disco."""

    def __init__(self, content: bytes, name: str, content_type: str = "image/jpeg"):
        super().__init__(content)
        self.name = name
        self.content_type = content_type


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"detail": message}, status=status)


def _json_ok_error(message: str, status: int = 400) -> JsonResponse:
    """
    Como _json_error, pero además incluye 'ok'/'message' — el shape que
    consumen los endpoints de carpetas/sync. 'detail' se mantiene para que
    los helpers genéricos de fetch del frontend (que leen payload.detail)
    sigan mostrando un mensaje limpio sin cambios adicionales.
    """
    return JsonResponse({"ok": False, "message": message, "detail": message}, status=status)


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


def _get_owned_cultivo(usuario, cultivo_id):
    return Cultivo.objects.filter(pk=cultivo_id, usuario=usuario).first()


def _serialize_asociacion(asoc: ImagenCultivo) -> dict:
    """
    Serializa una asociación imagen<->cultivo con los campos del asset ya
    aplanados adentro — mismo shape JSON que antes devolvía `_serialize()`
    sobre ImagenRepositorio directamente, para no romper el frontend
    (RepositoryGallery.tsx, contadores) ni el contrato de `/images/`.
    `id` es el id de la ASOCIACIÓN (ImagenCultivo), no el del asset global.
    """
    img = asoc.imagen
    return {
        "id": asoc.id,
        "asset_id": img.asset_id,
        "public_id": img.public_id,
        "secure_url": img.secure_url,
        "nombre_original": img.nombre_original,
        "formato": img.formato,
        "ancho": img.ancho,
        "alto": img.alto,
        "tamano_bytes": img.tamano_bytes,
        "asset_folder": img.asset_folder,
        "resource_type": img.resource_type,
        "fecha_creacion_cloudinary": img.fecha_creacion_cloudinary.isoformat() if img.fecha_creacion_cloudinary else None,
        "cultivo_id": asoc.cultivo_id,
        "lote_id": asoc.lote_id,
        "repositorio_id": img.repositorio_id,
        "estado": asoc.estado,
        "procesada": asoc.procesada,
        "analisis_id": asoc.analisis_id,
        "fecha_sincronizacion": asoc.fecha_asociacion.isoformat(),
        "fecha_procesamiento": asoc.fecha_procesamiento.isoformat() if asoc.fecha_procesamiento else None,
    }


# ==================== CONFIGURACIÓN DE REPOSITORIO ====================
# Nunca se serializa api_secret_cifrado ni el secreto en texto plano.


def _serialize_repositorio(config: RepositorioImagen, cantidad_imagenes: int | None = None) -> dict:
    return {
        "id": config.id,
        "nombre": config.nombre,
        "proveedor": config.proveedor,
        "cloud_name": config.cloud_name,
        "api_key": config.api_key,
        "carpeta_raiz": config.carpeta_raiz,
        "activo": config.activo,
        "estado_conexion": config.estado_conexion,
        "ultimo_sync": config.ultimo_sync.isoformat() if config.ultimo_sync else None,
        "fecha_creacion": config.fecha_creacion.isoformat(),
        "fecha_actualizacion": config.fecha_actualizacion.isoformat(),
        "cantidad_imagenes": (
            cantidad_imagenes if cantidad_imagenes is not None else config.imagenes.count()
        ),
    }


def _validar_payload_repositorio(data: dict, requerir_secret: bool = True):
    """Valida el payload de creación/edición de RepositorioImagen. Devuelve (campos, error_response)."""
    nombre = str(data.get("nombre", "")).strip()
    if not nombre:
        return None, _json_error("nombre es requerido.")
    if len(nombre) > 150:
        return None, _json_error("nombre no puede superar 150 caracteres.")

    proveedor = str(data.get("proveedor", RepositorioImagen.PROVEEDOR_CLOUDINARY)).strip().upper()
    if proveedor not in dict(RepositorioImagen.PROVEEDOR_CHOICES):
        return None, _json_error(
            f"proveedor inválido. Válidos: {[p[0] for p in RepositorioImagen.PROVEEDOR_CHOICES]}."
        )

    cloud_name = str(data.get("cloud_name", "")).strip()
    api_key = str(data.get("api_key", "")).strip()
    api_secret = str(data.get("api_secret", "")).strip()
    carpeta_raiz = str(data.get("carpeta_raiz", "")).strip()

    if not cloud_name or not api_key or (requerir_secret and not api_secret):
        return None, _json_error("cloud_name, api_key y api_secret son requeridos.")

    return {
        "nombre": nombre,
        "proveedor": proveedor,
        "cloud_name": cloud_name,
        "api_key": api_key,
        "api_secret": api_secret,
        "carpeta_raiz": carpeta_raiz,
    }, None


def _provider_para_payload(campos: dict) -> CloudinaryProvider:
    return CloudinaryProvider(campos["cloud_name"], campos["api_key"], campos["api_secret"], campos["carpeta_raiz"])


@csrf_exempt
def api_lista_repositorios(request):
    """
    GET /api/repository/config/  — lista los repositorios del usuario (sin secretos).
    POST /api/repository/config/ — crea uno nuevo:
      1. valida el payload;
      2. prueba la conexión real contra el proveedor (nunca guarda una config inválida);
      3. lo activa (desactiva cualquier otro repositorio activo del usuario);
      4. hace una consulta de descubrimiento (primera página de recursos) para
         mostrar cuántas imágenes hay disponibles — no persiste ImagenRepositorio
         todavía porque eso requiere elegir un cultivo (ver POST /api/repository/sync/).
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    if request.method == "GET":
        configs = RepositorioImagen.objects.filter(usuario=usuario).annotate(_cantidad=Count("imagenes"))
        return JsonResponse(
            {"results": [_serialize_repositorio(c, cantidad_imagenes=c._cantidad) for c in configs]},
            status=200,
        )

    if request.method == "POST":
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        campos, error_response = _validar_payload_repositorio(data)
        if error_response:
            return error_response

        provider = _provider_para_payload(campos)
        ok, mensaje = provider.test_connection()
        if not ok:
            return _json_error(mensaje, status=400)

        try:
            recursos_descubiertos, next_cursor = provider.list_resources(max_results=100)
        except RepositoryProviderError as exc:
            return _json_error(str(exc), status=502)

        with transaction.atomic():
            RepositorioImagen.objects.filter(usuario=usuario, activo=True).update(activo=False)
            config = RepositorioImagen(
                usuario=usuario,
                nombre=campos["nombre"],
                proveedor=campos["proveedor"],
                cloud_name=campos["cloud_name"],
                api_key=campos["api_key"],
                carpeta_raiz=campos["carpeta_raiz"],
                activo=True,
                estado_conexion="conectado",
            )
            config.set_api_secret(campos["api_secret"])
            config.save()

        return JsonResponse(
            {
                "repositorio": _serialize_repositorio(config, cantidad_imagenes=0),
                "descubrimiento": {
                    "cantidad_encontradas": len(recursos_descubiertos),
                    "hay_mas": next_cursor is not None,
                },
            },
            status=201,
        )

    return _json_error("Método no permitido.", status=405)


@csrf_exempt
def api_probar_conexion(request):
    """POST /api/repository/config/test/ — prueba credenciales sin persistir nada."""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    data, error_response = _parse_json_body(request)
    if error_response:
        return error_response

    campos, error_response = _validar_payload_repositorio(data)
    if error_response:
        return error_response

    provider = _provider_para_payload(campos)
    ok, mensaje = provider.test_connection()
    return JsonResponse({"ok": ok, "mensaje": mensaje}, status=200 if ok else 400)


def _get_owned_repositorio(usuario, repositorio_id):
    return RepositorioImagen.objects.filter(pk=repositorio_id, usuario=usuario).first()


@csrf_exempt
def api_detalle_repositorio(request, repositorio_id):
    """GET/PATCH /api/repository/config/<id>/"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    config = _get_owned_repositorio(usuario, repositorio_id)
    if config is None:
        return _json_error("El repositorio no existe o no pertenece al usuario.", status=404)

    if request.method == "GET":
        return JsonResponse(_serialize_repositorio(config), status=200)

    if request.method == "PATCH":
        data, error_response = _parse_json_body(request)
        if error_response:
            return error_response

        campos, error_response = _validar_payload_repositorio(data, requerir_secret=False)
        if error_response:
            return error_response

        secreto_nuevo = campos["api_secret"] or config.get_api_secret()
        provider = CloudinaryProvider(campos["cloud_name"], campos["api_key"], secreto_nuevo, campos["carpeta_raiz"])
        ok, mensaje = provider.test_connection()
        if not ok:
            return _json_error(mensaje, status=400)

        config.nombre = campos["nombre"]
        config.cloud_name = campos["cloud_name"]
        config.api_key = campos["api_key"]
        config.carpeta_raiz = campos["carpeta_raiz"]
        if campos["api_secret"]:
            config.set_api_secret(campos["api_secret"])
        config.estado_conexion = "conectado"
        config.save()

        return JsonResponse(_serialize_repositorio(config), status=200)

    return _json_error("Método no permitido.", status=405)


@csrf_exempt
def api_probar_conexion_repositorio(request, repositorio_id):
    """POST /api/repository/config/<id>/test/ — reprueba las credenciales ya guardadas."""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    config = _get_owned_repositorio(usuario, repositorio_id)
    if config is None:
        return _json_error("El repositorio no existe o no pertenece al usuario.", status=404)

    try:
        secreto = config.get_api_secret()
    except SecretDecryptionError as exc:
        return _json_error(str(exc), status=500)

    provider = CloudinaryProvider(config.cloud_name, config.api_key, secreto, config.carpeta_raiz)
    ok, mensaje = provider.test_connection()
    config.estado_conexion = "conectado" if ok else "fallido"
    config.save(update_fields=["estado_conexion", "fecha_actualizacion"])
    return JsonResponse({"ok": ok, "mensaje": mensaje}, status=200 if ok else 400)


@csrf_exempt
def api_activar_repositorio(request, repositorio_id):
    """POST /api/repository/config/<id>/activate/ — "Cambiar repositorio"."""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    config = _get_owned_repositorio(usuario, repositorio_id)
    if config is None:
        return _json_error("El repositorio no existe o no pertenece al usuario.", status=404)

    with transaction.atomic():
        RepositorioImagen.objects.filter(usuario=usuario, activo=True).exclude(pk=config.pk).update(activo=False)
        config.activo = True
        config.save(update_fields=["activo", "fecha_actualizacion"])

    return JsonResponse(_serialize_repositorio(config), status=200)


@csrf_exempt
def api_desactivar_repositorio(request, repositorio_id):
    """POST /api/repository/config/<id>/deactivate/"""
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    config = _get_owned_repositorio(usuario, repositorio_id)
    if config is None:
        return _json_error("El repositorio no existe o no pertenece al usuario.", status=404)

    config.activo = False
    config.save(update_fields=["activo", "fecha_actualizacion"])
    return JsonResponse(_serialize_repositorio(config), status=200)


# ==================== CARPETAS ====================


def api_lista_carpetas(request):
    """
    GET /api/repository/folders/

    Consulta en vivo (Admin API de Cloudinary) las carpetas disponibles en la
    cuenta del usuario — nunca depende de CLOUDINARY_FOLDER ni de reiniciar el
    backend: una carpeta creada en Cloudinary aparece aquí de inmediato.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "GET":
        return _json_ok_error("Método no permitido.", status=405)

    provider, _config = get_provider_for_user(usuario)
    if provider is None:
        return _json_ok_error("El repositorio externo no está configurado.", status=400)

    try:
        carpetas = provider.list_folders()
    except RepositoryProviderError:
        logger.exception("Error al consultar carpetas de Cloudinary (usuario_id=%s)", usuario.id)
        return _json_ok_error("No fue posible consultar las carpetas de Cloudinary.", status=502)

    return JsonResponse({"ok": True, "folders": carpetas}, status=200)


# ==================== SYNC ====================


@csrf_exempt
def api_sync(request):
    """
    POST /api/repository/sync/
    { "cultivo_id": 1 (opcional), "lote_id": 1 (opcional), "carpeta": "fresas2" (opcional) }

    Consulta Cloudinary (la carpeta indicada en `carpeta`, o si se omite la ya
    guardada en el repositorio activo del usuario) y hace upsert por
    public_id de cada asset en ImagenRepositorio (tabla global, sin dueño).
    Si se indica cultivo_id, además crea/reutiliza la asociación lógica
    ImagenCultivo(imagen, cultivo, usuario) — sin duplicarla si ya existe, y
    sin tocar asociaciones de otros cultivos/usuarios sobre el mismo asset:
    una misma imagen puede sincronizarse para varios cultivos sin perder el
    historial de ninguno. Si se indica `carpeta`, esa pasa a ser la carpeta
    guardada del repositorio (para que la próxima sincronización automática
    la recuerde).
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    data, error_response = _parse_json_body(request)
    if error_response:
        return error_response

    cultivo = None
    lote = None
    cultivo_id = data.get("cultivo_id")
    if cultivo_id:
        cultivo = _get_owned_cultivo(usuario, cultivo_id)
        if cultivo is None:
            return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

        lote_id = data.get("lote_id")
        if lote_id:
            lote = Lote.objects.filter(pk=lote_id, cultivo=cultivo).first()
            if lote is None:
                return _json_error("El lote no existe o no pertenece al cultivo indicado.", status=400)

    provider, config = get_provider_for_user(usuario)
    if provider is None:
        return _json_ok_error("El repositorio externo no está configurado.", status=400)

    carpeta_solicitada = data.get("carpeta")
    if carpeta_solicitada is not None:
        carpeta_solicitada = str(carpeta_solicitada).strip()
        provider.carpeta_raiz = carpeta_solicitada

    try:
        recursos = provider.list_all_resources()
    except RepositoryProviderError:
        logger.exception("Error al sincronizar con Cloudinary (usuario_id=%s)", usuario.id)
        if config is not None:
            config.estado_conexion = "fallido"
            config.save(update_fields=["estado_conexion", "fecha_actualizacion"])
        return _json_ok_error("No fue posible sincronizar las imágenes del repositorio externo.", status=502)

    # Se indexa por asset_id y por public_id (ambos únicos) para detectar
    # duplicados sin importar cuál identificador coincida.
    existentes_por_asset_id = {
        img.asset_id: img for img in ImagenRepositorio.objects.filter(
            asset_id__in=[r.get("asset_id") for r in recursos if r.get("asset_id")]
        )
    }
    existentes_por_public_id = {
        img.public_id: img for img in ImagenRepositorio.objects.filter(
            public_id__in=[r.get("public_id") for r in recursos if r.get("public_id")]
        )
    }

    assets_creados = 0
    assets_actualizados = 0
    asociadas = 0
    ya_asociadas = 0
    omitidas = 0

    for recurso in recursos:
        asset_id = recurso.get("asset_id")
        public_id = recurso.get("public_id")
        if not asset_id or not public_id:
            # Recurso sin datos suficientes para identificarlo — el único caso
            # real de "omitido" ahora (antes también se usaba para "ya
            # pertenece a otro cultivo", lo cual ya no aplica).
            omitidas += 1
            continue

        existente = existentes_por_asset_id.get(asset_id) or existentes_por_public_id.get(public_id)

        campos_cloudinary = {
            "secure_url": recurso.get("secure_url", ""),
            "formato": recurso.get("format", ""),
            "ancho": recurso.get("width"),
            "alto": recurso.get("height"),
            "tamano_bytes": recurso.get("bytes"),
            "asset_folder": recurso.get("asset_folder", "") or "",
            "resource_type": recurso.get("resource_type", "image") or "image",
            "fecha_creacion_cloudinary": _parse_fecha_cloudinary(recurso.get("created_at")),
        }

        if existente is not None:
            ImagenRepositorio.objects.filter(pk=existente.pk).update(**campos_cloudinary)
            imagen = existente
            assets_actualizados += 1
        else:
            imagen = ImagenRepositorio.objects.create(
                asset_id=asset_id,
                public_id=public_id,
                nombre_original=(
                    recurso.get("filename") or recurso.get("display_name") or recurso.get("original_filename", "")
                ),
                repositorio=config,
                **campos_cloudinary,
            )
            existentes_por_asset_id[asset_id] = imagen
            existentes_por_public_id[public_id] = imagen
            assets_creados += 1

        if cultivo is not None:
            asociacion, creada = ImagenCultivo.objects.get_or_create(
                imagen=imagen, cultivo=cultivo, usuario=usuario, defaults={"lote": lote},
            )
            if creada:
                asociadas += 1
            else:
                ya_asociadas += 1
                if lote is not None and asociacion.lote_id != lote.id:
                    asociacion.lote = lote
                    asociacion.save(update_fields=["lote"])

    if config is not None:
        campos_actualizar = ["estado_conexion", "ultimo_sync", "fecha_actualizacion"]
        config.estado_conexion = "conectado"
        config.ultimo_sync = timezone.now()
        if carpeta_solicitada is not None and carpeta_solicitada != config.carpeta_raiz:
            config.carpeta_raiz = carpeta_solicitada
            campos_actualizar.append("carpeta_raiz")
        config.save(update_fields=campos_actualizar)

    carpeta_sincronizada = carpeta_solicitada if carpeta_solicitada is not None else (config.carpeta_raiz if config else "")
    total_cloudinary = len(recursos)
    total_visible_for_crop = ImagenCultivo.objects.filter(cultivo=cultivo).count() if cultivo is not None else 0

    if total_cloudinary == 0:
        mensaje = "La carpeta seleccionada no tiene imágenes."
    elif cultivo is None:
        mensaje = "Las imágenes fueron sincronizadas en el repositorio, pero no se asociaron a un cultivo porque no se seleccionó ninguno."
    elif asociadas > 0:
        mensaje = "Sincronización completada correctamente. Las imágenes quedaron asociadas al cultivo seleccionado."
    elif ya_asociadas > 0:
        mensaje = "Las imágenes ya estaban asociadas a este cultivo. No se crearon duplicados."
    else:
        mensaje = "La sincronización terminó sin imágenes nuevas."

    return JsonResponse(
        {
            "ok": True,
            "folder": carpeta_sincronizada,
            "total_cloudinary": total_cloudinary,
            "created_assets": assets_creados,
            "updated_assets": assets_actualizados,
            "associated": asociadas,
            "already_associated": ya_asociadas,
            "skipped": omitidas,
            "total_visible_for_crop": total_visible_for_crop,
            "message": mensaje,
            # Campos históricos — se conservan para no romper otros consumidores.
            "total": total_cloudinary,
            "creadas": [],
            "cantidad_creadas": assets_creados,
            "cantidad_actualizadas": assets_actualizados,
        },
        status=200,
    )


# ==================== IMÁGENES ====================


def api_lista_imagenes(request):
    """
    GET /api/repository/images/?cultivo_id=&lote_id=&estado=&page=&page_size=

    `resumen` se calcula sobre cultivo_id/lote_id (sin aplicar el filtro
    `estado`) para que siempre refleje los 4 conteos completos, sin importar
    qué estado esté filtrando la página actual.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    cultivo_id = request.GET.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")

    # Galería = asociaciones (ImagenCultivo) del cultivo, no assets globales:
    # una misma imagen puede estar disponible aquí y ya procesada en otro
    # cultivo, así que el estado/contador siempre se lee de la asociación.
    base = ImagenCultivo.objects.filter(
        cultivo_id=cultivo_id, cultivo__usuario=usuario,
    ).select_related("imagen", "cultivo", "lote")

    lote_id = request.GET.get("lote_id")
    if lote_id:
        base = base.filter(lote_id=lote_id)

    resumen = base.aggregate(
        total=Count("id"),
        pendientes=Count("id", filter=Q(estado="disponible")),
        procesando=Count("id", filter=Q(estado="procesando")),
        procesadas=Count("id", filter=Q(estado="procesada")),
        con_error=Count("id", filter=Q(estado="error")),
    )

    asociaciones = base
    estado = request.GET.get("estado")
    if estado:
        asociaciones = asociaciones.filter(estado=estado)

    try:
        page = max(int(request.GET.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        page_size = 20

    total = asociaciones.count()
    start = (page - 1) * page_size
    pagina = asociaciones[start:start + page_size]

    return JsonResponse(
        {
            "results": [_serialize_asociacion(a) for a in pagina],
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max((total + page_size - 1) // page_size, 1),
            "resumen": resumen,
        },
        status=200,
    )


@csrf_exempt
def api_subir_imagen(request):
    """
    POST /api/repository/images/upload/
    multipart/form-data: cultivo_id, lote_id (opcional), imagenes[] (>=1)

    Sube directamente a Cloudinary (no queda copia local) y crea el registro.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response
    if request.method != "POST":
        return _json_error("Método no permitido.", status=405)

    cultivo_id = request.POST.get("cultivo_id")
    if not cultivo_id:
        return _json_error("cultivo_id es requerido.")
    cultivo = _get_owned_cultivo(usuario, cultivo_id)
    if cultivo is None:
        return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

    lote_id = request.POST.get("lote_id") or None
    lote = None
    if lote_id:
        lote = Lote.objects.filter(pk=lote_id, cultivo=cultivo).first()
        if lote is None:
            return _json_error("El lote no existe o no pertenece al cultivo indicado.", status=400)

    imagenes = request.FILES.getlist("imagenes")
    if not imagenes:
        return _json_error("Se requiere al menos una imagen en el campo 'imagenes'.")

    for archivo in imagenes:
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in services.EXTENSIONES_VALIDAS:
            return _json_error(
                f"Archivo '{archivo.name}' no válido. "
                f"Solo se aceptan: {', '.join(sorted(services.EXTENSIONES_VALIDAS))}."
            )

    provider, config = get_provider_for_user(usuario)
    if provider is None:
        return _json_error(
            "No tienes un repositorio de imágenes configurado. Configura uno en el módulo Repositorio.",
            status=400,
        )

    creadas = []
    try:
        for archivo in imagenes:
            recurso = provider.upload(archivo)
            imagen = ImagenRepositorio.objects.create(
                asset_id=recurso["asset_id"],
                public_id=recurso["public_id"],
                secure_url=recurso.get("secure_url", ""),
                nombre_original=archivo.name,
                formato=recurso.get("format", ""),
                ancho=recurso.get("width"),
                alto=recurso.get("height"),
                tamano_bytes=recurso.get("bytes"),
                asset_folder=recurso.get("asset_folder", "") or "",
                resource_type=recurso.get("resource_type", "image") or "image",
                fecha_creacion_cloudinary=_parse_fecha_cloudinary(recurso.get("created_at")),
                repositorio=config,
            )
            asociacion = ImagenCultivo.objects.create(
                imagen=imagen, cultivo=cultivo, lote=lote, usuario=usuario,
            )
            creadas.append(_serialize_asociacion(asociacion))
    except RepositoryProviderError as exc:
        return _json_error(str(exc), status=502)

    return JsonResponse({"results": creadas}, status=201)


@csrf_exempt
def api_detalle_imagen(request, imagen_id):
    """
    GET/DELETE /api/repository/images/<id>/

    `imagen_id` identifica la ASOCIACIÓN (ImagenCultivo), no el asset global
    — es el mismo id que ya devuelve `/images/` en `results[].id`.
    """
    usuario, error_response = _get_authenticated_user(request)
    if error_response:
        return error_response

    asociacion = get_object_or_404(
        ImagenCultivo.objects.select_related("imagen", "cultivo", "lote"),
        pk=imagen_id,
        cultivo__usuario=usuario,
    )

    if request.method == "GET":
        return JsonResponse(_serialize_asociacion(asociacion), status=200)

    if request.method == "DELETE":
        imagen = asociacion.imagen
        asociacion.delete()

        # Solo se borra el asset de Cloudinary (y la fila global) cuando esta
        # era su última asociación — si sigue vinculado a otro cultivo, ese
        # cultivo no debe perder la imagen por una eliminación ajena.
        if not imagen.asociaciones.exists():
            provider, _config = get_provider_for_user(usuario)
            if provider is not None:
                try:
                    provider.delete(imagen.public_id)
                except RepositoryProviderError as exc:
                    return _json_error(str(exc), status=502)
            imagen.delete()

        return JsonResponse({"deleted": True, "id": imagen_id}, status=200)

    return _json_error("Método no permitido.", status=405)


# ==================== PROCESAMIENTO ====================


@csrf_exempt
def api_procesar_imagenes(request):
    """
    POST /api/repository/images/process/
    { "cultivo_id": 1, "lote_id": 1 (opcional), "image_ids": [1,2,3], "notas": "" (opcional) }

    Recupera las imágenes por ID (secure_url ya guardada en BD, nunca enviada
    por el cliente), corre Mask R-CNN, persiste Analisis/Metrica y descarta
    los bytes temporales (nunca se escriben a disco).
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
    cultivo = _get_owned_cultivo(usuario, cultivo_id)
    if cultivo is None:
        return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

    lote_id = data.get("lote_id")
    lote = None
    if lote_id:
        lote = Lote.objects.filter(pk=lote_id, cultivo=cultivo).first()
        if lote is None:
            return _json_error("El lote no existe o no pertenece al cultivo indicado.", status=400)

    image_ids = data.get("image_ids")
    if not image_ids or not isinstance(image_ids, list):
        return _json_error("image_ids debe ser una lista con al menos un ID.")

    # image_ids referencia asociaciones (ImagenCultivo), no assets globales —
    # así el mismo asset puede procesarse de forma independiente en otro
    # cultivo sin que un procesamiento pise el estado/resultado del otro.
    asociaciones_db = list(
        ImagenCultivo.objects.filter(id__in=image_ids, cultivo=cultivo).select_related("imagen")
    )
    if len(asociaciones_db) != len(set(image_ids)):
        return _json_error("Alguna imagen no existe o no pertenece al cultivo indicado.", status=400)

    ids_asociaciones = [a.id for a in asociaciones_db]
    ImagenCultivo.objects.filter(id__in=ids_asociaciones).update(estado="procesando")

    # Repositorio de origen de este lote (asumimos uno solo — las imágenes de
    # un mismo cultivo se sincronizan normalmente desde el mismo repositorio).
    repositorio_origen = next(
        (a.imagen.repositorio for a in asociaciones_db if a.imagen.repositorio_id), None
    )

    # Se crea de inmediato en estado "procesando": el historial refleja el
    # trabajo en curso (no solo el resultado final) y created_at queda como
    # inicio real del procesamiento — usado para calcular la duración.
    analisis = Analisis.objects.create(
        usuario=usuario,
        cultivo=cultivo,
        lote=lote,
        repositorio=repositorio_origen,
        origen="repositorio",
        estado="procesando",
        cantidad_imagenes=len(asociaciones_db),
    )

    def _registrar_error(mensaje: str) -> None:
        ImagenCultivo.objects.filter(id__in=ids_asociaciones).update(estado="error")
        analisis.estado = "error"
        analisis.mensaje_error = mensaje
        analisis.save(update_fields=["estado", "mensaje_error", "updated_at"])

    try:
        archivos = []
        for asoc in asociaciones_db:
            img = asoc.imagen
            contenido = services.descargar_bytes(img.secure_url)
            nombre = img.nombre_original or f"{img.public_id}.{img.formato or 'jpg'}"
            archivos.append(_MemoryImageFile(contenido, nombre))

        service_output = process_images(
            archivos=archivos,
            cultivo_id=cultivo.id,
            lote_id=lote.id if lote else None,
            notas=str(data.get("notas", "")),
        )
    except services.CloudinaryServiceError as exc:
        _registrar_error(str(exc))
        return _json_error(str(exc), status=502)
    except ProcesamientoError as exc:
        _registrar_error(str(exc))
        return _json_error(str(exc), status=400)
    except Exception as exc:
        logger.exception("Error al procesar imágenes (repositorio, cultivo_id=%s)", cultivo.id)
        _registrar_error("El procesamiento no pudo completarse.")
        return _json_error("El procesamiento no pudo completarse.", status=500)

    resultado_json = service_output["resultado_json"]
    imagen_urls = [{"url": a.imagen.secure_url, "nombre": a.imagen.nombre_original} for a in asociaciones_db]
    fecha_ahora = timezone.now()
    tipos_validos = [t[0] for t in Metrica.TIPOS_RESULTADO]
    metricas_creadas = []

    try:
        with transaction.atomic():
            analisis.estado = "procesado"
            analisis.imagen_urls = imagen_urls
            analisis.cantidad_frutos = resultado_json.get("cantidad_frutos", {}).get("valor")
            analisis.frutos_maduros = resultado_json.get("frutos_maduros", {}).get("valor")
            analisis.porcentaje_madurez = _decimal_o_none(resultado_json.get("porcentaje_madurez", {}).get("valor"))
            analisis.estimacion_cosecha = _decimal_o_none(resultado_json.get("estimacion_cosecha", {}).get("valor"))
            analisis.notas = service_output.get("notas", "")
            analisis.resultado_json = resultado_json
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
                        f"Procesado desde el repositorio Cloudinary "
                        f"({len(asociaciones_db)} imagen{'es' if len(asociaciones_db) != 1 else ''})."
                    ),
                    fuente="modelo_vision",
                )
                metrica.save()
                metricas_creadas.append(metrica.id)

            ImagenCultivo.objects.filter(id__in=ids_asociaciones).update(
                estado="procesada",
                procesada=True,
                fecha_procesamiento=fecha_ahora,
                analisis=analisis,
            )
    except ValidationError as exc:
        _registrar_error("; ".join(exc.messages))
        return _json_error("; ".join(exc.messages), status=400)

    duracion_segundos = (analisis.updated_at - analisis.created_at).total_seconds()

    return JsonResponse(
        {
            "analisis_id": analisis.id,
            "status": "COMPLETADO",
            "metricas_creadas": len(metricas_creadas),
            "modelo_usado": service_output.get("modelo_usado", "unknown"),
            "imagenes_procesadas": service_output["imagenes_procesadas"],
            "duracion_segundos": round(duracion_segundos, 3),
            "metrics": {
                clave: datos.get("valor")
                for clave, datos in resultado_json.items()
                if clave in tipos_validos
            },
        },
        status=201,
    )


@csrf_exempt
def api_procesar_repositorio(request):
    """
    POST /api/repository/process-all/
    { "cultivo_id": 13, "lote_id": null (opcional) }

    Procesa automáticamente TODAS las imágenes en estado "disponible"
    (pendiente) del cultivo indicado — el cliente nunca envía image_ids.
    No se reprocesan por defecto imágenes ya "procesada" ni "error".

    A diferencia de api_procesar_imagenes, cada imagen se descarga y corre
    por Mask R-CNN de forma independiente (una llamada a process_images por
    imagen, nunca un batch con todo el repositorio a la vez): evita cargar
    todo en memoria y el fallo de una imagen no cancela las demás.
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
    cultivo = _get_owned_cultivo(usuario, cultivo_id)
    if cultivo is None:
        return _json_error("El cultivo no existe o no pertenece al usuario.", status=404)

    lote_id = data.get("lote_id")
    lote = None
    if lote_id:
        lote = Lote.objects.filter(pk=lote_id, cultivo=cultivo).first()
        if lote is None:
            return _json_error("El lote no existe o no pertenece al cultivo indicado.", status=400)

    asociaciones_qs = ImagenCultivo.objects.filter(cultivo=cultivo, estado="disponible").select_related("imagen")
    if lote is not None:
        asociaciones_qs = asociaciones_qs.filter(lote=lote)
    asociaciones_pendientes = list(asociaciones_qs.order_by("fecha_asociacion"))

    if not asociaciones_pendientes:
        return JsonResponse(
            {
                "status": "SIN_PENDIENTES",
                "message": "No hay imágenes pendientes por procesar.",
                "cultivo_id": cultivo.id,
                "imagenes_procesadas": 0,
                "imagenes_con_error": 0,
            },
            status=200,
        )

    # Repositorio de origen del lote (asumimos uno solo — ver api_procesar_imagenes).
    repositorio_origen = next(
        (a.imagen.repositorio for a in asociaciones_pendientes if a.imagen.repositorio_id), None
    )

    ids_pendientes = [a.id for a in asociaciones_pendientes]
    ImagenCultivo.objects.filter(id__in=ids_pendientes).update(estado="procesando")

    analisis = Analisis.objects.create(
        usuario=usuario,
        cultivo=cultivo,
        lote=lote,
        repositorio=repositorio_origen,
        origen="repositorio",
        estado="procesando",
        cantidad_imagenes=len(asociaciones_pendientes),
    )

    total_frutos = 0
    total_maduros = 0
    total_cosecha = 0.0
    imagen_urls = []
    ids_ok = []
    errores = []
    modelo_usado = "unknown"

    for asoc in asociaciones_pendientes:
        img = asoc.imagen
        try:
            contenido = services.descargar_bytes(img.secure_url)
            nombre = img.nombre_original or f"{img.public_id}.{img.formato or 'jpg'}"
            archivo = _MemoryImageFile(contenido, nombre)

            resultado = process_images(archivos=[archivo], cultivo_id=cultivo.id, lote_id=lote.id if lote else None)
            resultado_json_img = resultado["resultado_json"]
            modelo_usado = resultado.get("modelo_usado", modelo_usado)

            # Consolidación: se suman las 3 métricas base ya calculadas por la
            # lógica existente (nunca se reinventa la fórmula de cosecha) —
            # el porcentaje de madurez se recalcula sobre los totales al final,
            # nunca se promedian los porcentajes individuales.
            total_frutos += resultado_json_img.get("cantidad_frutos", {}).get("valor", 0) or 0
            total_maduros += resultado_json_img.get("frutos_maduros", {}).get("valor", 0) or 0
            total_cosecha += resultado_json_img.get("estimacion_cosecha", {}).get("valor", 0) or 0

            fecha_ahora = timezone.now()
            ImagenCultivo.objects.filter(id=asoc.id).update(
                estado="procesada", procesada=True, fecha_procesamiento=fecha_ahora, analisis=analisis,
            )
            imagen_urls.append({"url": img.secure_url, "nombre": img.nombre_original})
            ids_ok.append(asoc.id)
        except (services.CloudinaryServiceError, ProcesamientoError) as exc:
            ImagenCultivo.objects.filter(id=asoc.id).update(estado="error")
            errores.append({"imagen_id": asoc.id, "motivo": str(exc)})
        except Exception as exc:
            logger.exception("Error al procesar imagen (repositorio, asociacion_id=%s)", asoc.id)
            ImagenCultivo.objects.filter(id=asoc.id).update(estado="error")
            errores.append({"imagen_id": asoc.id, "motivo": "No fue posible procesar esta imagen."})

    if not ids_ok:
        analisis.estado = "error"
        analisis.mensaje_error = f"Fallaron las {len(errores)} imagen(es) pendientes."
        analisis.save(update_fields=["estado", "mensaje_error", "updated_at"])
        return JsonResponse(
            {
                "analisis_id": analisis.id,
                "status": "ERROR",
                "message": "No fue posible completar el procesamiento.",
                "cultivo_id": cultivo.id,
                "imagenes_procesadas": 0,
                "imagenes_con_error": len(errores),
                "errores": errores,
            },
            status=502,
        )

    porcentaje_madurez = round((total_maduros / total_frutos) * 100, 2) if total_frutos > 0 else None
    total_cosecha = round(total_cosecha, 3)

    resultado_consolidado = {
        "cantidad_frutos": {"valor": total_frutos, "unidad": "unidades"},
        "frutos_maduros": {"valor": total_maduros, "unidad": "unidades"},
        "estimacion_cosecha": {"valor": total_cosecha, "unidad": "kg"},
        "debug": {
            "imagenes_procesadas_ids": ids_ok,
            "imagenes_con_error": errores,
            "modelo": modelo_usado,
        },
    }
    if porcentaje_madurez is not None:
        resultado_consolidado["porcentaje_madurez"] = {"valor": porcentaje_madurez, "unidad": "%"}

    tipos_validos = [t[0] for t in Metrica.TIPOS_RESULTADO]
    fecha_ahora = timezone.now()
    estado_final = "procesado" if not errores else "procesado_con_errores"

    with transaction.atomic():
        analisis.estado = estado_final
        analisis.imagen_urls = imagen_urls
        analisis.cantidad_frutos = total_frutos
        analisis.frutos_maduros = total_maduros
        analisis.porcentaje_madurez = _decimal_o_none(porcentaje_madurez)
        analisis.estimacion_cosecha = _decimal_o_none(total_cosecha)
        analisis.resultado_json = resultado_consolidado
        if errores:
            analisis.mensaje_error = f"{len(errores)} de {len(asociaciones_pendientes)} imagen(es) fallaron."
        analisis.full_clean()
        analisis.save()

        for tipo, datos in resultado_consolidado.items():
            if tipo not in tipos_validos:
                continue
            Metrica.objects.create(
                cultivo=cultivo,
                lote=lote,
                tipo_resultado=tipo,
                valor=Decimal(str(datos["valor"])),
                unidad=datos["unidad"],
                fecha_registro=fecha_ahora,
                descripcion=(
                    f"Procesamiento automático del repositorio ({len(ids_ok)} imagen{'es' if len(ids_ok) != 1 else ''}"
                    f"{f', {len(errores)} con error' if errores else ''})."
                ),
                fuente="modelo_vision",
            )

    duracion_segundos = (analisis.updated_at - analisis.created_at).total_seconds()

    return JsonResponse(
        {
            "analisis_id": analisis.id,
            "status": "COMPLETADO" if estado_final == "procesado" else "COMPLETADO_CON_ERRORES",
            "cultivo_id": cultivo.id,
            "imagenes_procesadas": len(ids_ok),
            "imagenes_con_error": len(errores),
            "errores": errores,
            "duracion_segundos": round(duracion_segundos, 3),
            "modelo_usado": modelo_usado,
            "metrics": {
                "cantidad_frutos": total_frutos,
                "frutos_maduros": total_maduros,
                "porcentaje_madurez": porcentaje_madurez,
                "estimacion_cosecha": total_cosecha,
            },
        },
        status=201,
    )
