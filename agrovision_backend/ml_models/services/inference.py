"""
AgroVision OS - Inference Service
Ejecuta el modelo Mask R-CNN real sobre imágenes y retorna métricas de cultivos.
"""

from typing import List

import numpy as np

from .model_loader import ModeloNoDisponibleError, get_model_loader

MASK_BINARY_THRESHOLD = 0.5


class InferenceError(Exception):
    """Error durante la inferencia."""
    pass


def procesar_imagenes(archivos_o_batch) -> dict:
    """
    Ejecuta Mask R-CNN (torchvision, ResNet-50 FPN) y retorna métricas reales.

    Acepta:
    - Lista de archivos subidos (Django UploadedFile) -> lee internamente
    - Array numpy (batch preprocesado, HxWx3 uint8 o float [0,1]) -> infiere directamente

    Returns:
        dict con métricas (cantidad_frutos, frutos_maduros, estimacion_cosecha
        y, si hubo al menos una detección, porcentaje_madurez) y bloque debug.

    Raises:
        ModeloNoDisponibleError: Si no se puede cargar el modelo.
        InferenceError: Si falla la pipeline de inferencia.
    """
    from ml_models.utils.image_utils import (
        EXTENSIONES_VALIDAS,
        leer_desde_bytes,
        redimensionar,
        validar_extension,
    )
    from ml_models.services.metrics import AVG_WEIGHT_PER_FRUIT_G, SCORE_THRESHOLD

    es_lista_archivos = not isinstance(archivos_o_batch, np.ndarray)

    if es_lista_archivos:
        archivos = list(archivos_o_batch)
        if not archivos:
            raise InferenceError("No se recibieron archivos de imagen.")

        for archivo in archivos:
            nombre = getattr(archivo, "name", "unknown")
            if not validar_extension(nombre):
                raise InferenceError(
                    f"Archivo '{nombre}' no tiene extensión válida. "
                    f"Extensiones aceptadas: {sorted(EXTENSIONES_VALIDAS)}"
                )

        imagenes = []
        for archivo in archivos:
            contenido = archivo.read()
            arr = leer_desde_bytes(contenido)
            arr = redimensionar(arr)  # (640, 640, 3) uint8, letterbox
            imagenes.append(arr)
            archivo.seek(0)

        batch = np.stack(imagenes) if imagenes else np.array([])
    else:
        batch = archivos_o_batch
        if batch.size and batch.dtype != np.uint8:
            batch = np.clip(batch * 255.0, 0, 255).astype(np.uint8)

    n_imagenes = len(batch)
    if n_imagenes == 0:
        raise InferenceError("No hay imágenes para procesar.")

    try:
        loader = get_model_loader()
        modelo = loader.modelo
        device = loader.device
    except ModeloNoDisponibleError:
        raise
    except Exception as exc:
        raise ModeloNoDisponibleError(f"No se pudo cargar el modelo: {exc}") from exc

    try:
        return _ejecutar_inferencia_real(batch, modelo, AVG_WEIGHT_PER_FRUIT_G, SCORE_THRESHOLD, device)
    except (InferenceError, ModeloNoDisponibleError):
        raise
    except Exception as exc:
        raise InferenceError(f"Error durante la inferencia: {exc}") from exc


def _clasificar_madurez(imagen_uint8: np.ndarray, mascara_binaria: np.ndarray) -> dict:
    """
    Heurística de color para decidir si un fruto detectado está maduro.
    Ver nota en ml_models/services/metrics.py sobre el origen de los umbrales.
    """
    from ml_models.services.metrics import RIPE_MEAN_RED_MIN, RIPE_RED_RATIO_THRESHOLD

    pixeles = imagen_uint8[mascara_binaria]
    if pixeles.size == 0:
        return {"maduro": False, "mean_red": 0.0, "red_ratio": 0.0}

    r = pixeles[:, 0].astype(np.float32)
    g = pixeles[:, 1].astype(np.float32)
    b = pixeles[:, 2].astype(np.float32)

    mean_red = float(r.mean())
    red_ratio = float(((r > g) & (r > b)).mean())

    maduro = mean_red >= RIPE_MEAN_RED_MIN and red_ratio >= RIPE_RED_RATIO_THRESHOLD
    return {"maduro": maduro, "mean_red": mean_red, "red_ratio": red_ratio}


def _ejecutar_inferencia_real(
    batch: np.ndarray,
    modelo,
    avg_weight_per_fruit_g: float,
    score_threshold: float,
    device=None,
) -> dict:
    import torch

    n_imagenes = len(batch)
    tensores = [
        torch.from_numpy(img.astype(np.float32) / 255.0).permute(2, 0, 1)
        for img in batch
    ]
    if device is not None:
        tensores = [t.to(device) for t in tensores]

    with torch.no_grad():
        salidas = modelo(tensores)

    cantidad_frutos = 0
    frutos_maduros = 0
    scores_filtrados_debug: List[float] = []
    boxes_filtrados_debug: List[List[float]] = []

    for idx_imagen, salida in enumerate(salidas):
        scores = salida["scores"]
        boxes = salida["boxes"]
        masks = salida["masks"]
        h, w = batch[idx_imagen].shape[:2]

        indices_validos = (scores >= score_threshold).nonzero(as_tuple=True)[0]

        for idx in indices_validos.tolist():
            cantidad_frutos += 1
            mascara_binaria = (masks[idx, 0] >= MASK_BINARY_THRESHOLD).detach().cpu().numpy()
            clasificacion = _clasificar_madurez(batch[idx_imagen], mascara_binaria)
            if clasificacion["maduro"]:
                frutos_maduros += 1

            if idx_imagen == 0:
                x1, y1, x2, y2 = boxes[idx].detach().cpu().tolist()
                boxes_filtrados_debug.append([x1 / w, y1 / h, x2 / w, y2 / h])
                scores_filtrados_debug.append(round(float(scores[idx]), 4))

    resultado = {
        "cantidad_frutos": {"valor": cantidad_frutos, "unidad": "unidades"},
        "frutos_maduros": {"valor": frutos_maduros, "unidad": "unidades"},
        "estimacion_cosecha": {
            "valor": round((frutos_maduros * avg_weight_per_fruit_g) / 1000.0, 3),
            "unidad": "kg",
        },
        "debug": {
            "total_imagenes_procesadas": n_imagenes,
            "score_threshold_usado": score_threshold,
            "avg_weight_per_fruit_g_usado": avg_weight_per_fruit_g,
            "scores_filtrados": scores_filtrados_debug,
            "boxes_filtrados": boxes_filtrados_debug,
            "modelo": "maskrcnn_resnet50_fpn",
        },
    }

    # Sin detecciones no hay base para calcular un porcentaje — se omite la
    # clave en vez de reportar 0% como si fuera una medición real.
    if cantidad_frutos > 0:
        resultado["porcentaje_madurez"] = {
            "valor": round((frutos_maduros / cantidad_frutos) * 100.0, 2),
            "unidad": "%",
        }

    return resultado
