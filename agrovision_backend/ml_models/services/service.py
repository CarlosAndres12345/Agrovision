"""
AgroVision OS - Service
Punto de entrada principal del módulo ML.
Une carga del modelo, preprocesamiento, inferencia y métricas.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ml_models.services.inference import procesar_imagenes, InferenceError
from ml_models.services.model_loader import ModeloNoDisponibleError
from ml_models.services.metrics import formatear_para_respuesta
from ml_models.utils.config import DEFAULT_MODEL_PATH, EXTENSIONES_VALIDAS
from ml_models.utils.image_utils import leer_desde_bytes, redimensionar, normalizar, validar_extension


class ProcesamientoError(Exception):
    """Error general en el pipeline de procesamiento."""
    pass


def _validar_archivos(archivos: list) -> None:
    if not archivos:
        raise ProcesamientoError("No se recibieron archivos de imagen.")

    for archivo in archivos:
        nombre = getattr(archivo, "name", "unknown")
        if not validar_extension(nombre):
            raise ProcesamientoError(
                f"Archivo '{nombre}' no tiene extensión válida. "
                f"Extensiones aceptadas: {sorted(EXTENSIONES_VALIDAS)}"
            )


def _preprocesar(archivos: list) -> list:
    salida = []
    for archivo in archivos:
        contenido = archivo.read()
        arr = leer_desde_bytes(contenido)
        arr = redimensionar(arr)
        arr = normalizar(arr)
        salida.append(arr)
        archivo.seek(0)
    return salida


def process_images(
    archivos: list,
    cultivo_id: int,
    lote_id: Optional[int] = None,
    notas: str = "",
) -> dict:
    """
    Pipeline: valida extensiones, delega a inferencia y formatea métricas.

    Args:
        archivos: Lista de archivos de imagen (Django UploadedFile o similar).
        cultivo_id: ID del cultivo asociado.
        lote_id: ID del lote asociado (opcional).
        notas: Notas adicionales del análisis.

    Returns:
        dict listo para persistir en Analisis/Metrica.

    Raises:
        ProcesamientoError: Si falla cualquier etapa del pipeline.
    """
    _validar_archivos(archivos)

    # Asegurar que los archivos estén al inicio antes de leerlos en inferencia
    for archivo in archivos:
        archivo.seek(0)

    try:
        resultados = procesar_imagenes(list(archivos))
    except ModeloNoDisponibleError as exc:
        # No hay checkpoint físico en este entorno (p. ej. no se sube al
        # desplegar por su tamaño) — nunca se simula un resultado: se informa
        # con un mensaje claro y se corta el flujo aquí.
        raise ProcesamientoError(
            "El modelo de visión computacional no está disponible en este entorno."
        ) from exc
    except InferenceError as exc:
        raise ProcesamientoError(f"Error en inferencia: {exc}") from exc

    return {
        "cultivo_id": cultivo_id,
        "lote_id": lote_id,
        "imagenes_procesadas": len(archivos),
        "metricas": formatear_para_respuesta(resultados),
        "resultado_json": resultados,
        "imagenes_nombres": [getattr(a, "name", "unknown") for a in archivos],
        "notas": notas.strip(),
        "modelo_usado": str(DEFAULT_MODEL_PATH.name),
    }
