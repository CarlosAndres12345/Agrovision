"""
AgroVision OS - Utilidades de imagen.
Carga, validación y preprocesamiento de imágenes para el modelo.
"""

from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image


EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def validar_extension(nombre_archivo: str) -> bool:
    """Verifica si la extensión del archivo es una imagen válida."""
    return Path(nombre_archivo).suffix.lower() in EXTENSIONES_VALIDAS


def leer_bytes(contenido: bytes) -> np.ndarray:
    """
    Lee bytes de una imagen y retorna un array numpy RGB.

    Args:
        contenido: Bytes crudos del archivo de imagen.

    Returns:
        Array numpy en formato RGB (H, W, 3).
    """
    imagen = Image.open(contenido)
    if imagen.mode != "RGB":
        imagen = imagen.convert("RGB")
    return np.array(imagen)


def leer_desde_bytes(contenido: bytes) -> np.ndarray:
    """
    Lee imagen desde bytes (compatible con Django UploadedFile.read()).

    Args:
        contenido: Bytes de la imagen.

    Returns:
        Array numpy RGB.
    """
    from io import BytesIO
    return leer_bytes(BytesIO(contenido))


def leer_desde_ruta(ruta: Path) -> np.ndarray:
    """
    Lee imagen desde ruta de archivo.

    Args:
        ruta: Path del archivo de imagen.

    Returns:
        Array numpy RGB.
    """
    imagen = Image.open(ruta)
    if imagen.mode != "RGB":
        imagen = imagen.convert("RGB")
    return np.array(imagen)


def redimensionar(imagen: np.ndarray, tamaño: int = 640) -> np.ndarray:
    """
    Redimensiona imagen manteniendo aspecto, rellenando con negro.

    Args:
        imagen: Array numpy de la imagen.
        tamaño: Tamaño objetivo (cuadrado).

    Returns:
        Imagen redimensionada a (tamaño, tamaño, 3).
    """
    h, w = imagen.shape[:2]
    escala = tamaño / max(h, w)
    nuevo_h, nuevo_w = int(h * escala), int(w * escala)

    pil_img = Image.fromarray(imagen)
    pil_img = pil_img.resize((nuevo_w, nuevo_h), Image.Resampling.BILINEAR)

    canvas = Image.new("RGB", (tamaño, tamaño), (0, 0, 0))
    canvas.paste(pil_img, ((tamaño - nuevo_w) // 2, (tamaño - nuevo_h) // 2))

    return np.array(canvas)


def normalizar(imagen: np.ndarray) -> np.ndarray:
    """
    Normaliza imagen a rango [0, 1] en float32.

    Args:
        imagen: Array numpy uint8.

    Returns:
        Array numpy float32 en rango [0, 1].
    """
    return imagen.astype(np.float32) / 255.0


def preprocesar_batch(
    archivos: list,
    tamaño: int = 640,
) -> Tuple[np.ndarray, List[str]]:
    """
    Pipeline completo: lee, redimensiona y normaliza una lista de archivos.

    Args:
        archivos: Lista de archivos (Django UploadedFile o similar).
        tamaño: Tamaño objetivo de redimensionado.

    Returns:
        (batch, nombres): batch numpy shape (N, H, W, 3) y lista de nombres.
    """
    nombres = []
    imagenes = []

    for archivo in archivos:
        nombre = getattr(archivo, "name", "unknown")
        if not validar_extension(nombre):
            from ml_models.services.inference import InferenceError
            raise InferenceError(
                f"Archivo '{nombre}' no tiene extensión válida. "
                f"Extensiones aceptadas: {sorted(EXTENSIONES_VALIDAS)}"
            )

        contenido = archivo.read()
        arr = leer_desde_bytes(contenido)
        arr = redimensionar(arr, tamaño)
        arr = normalizar(arr)
        imagenes.append(arr)
        nombres.append(nombre)
        archivo.seek(0)

    batch = np.stack(imagenes) if imagenes else np.array([])
    return batch, nombres


def imagen_a_tensor(imagen: np.ndarray) -> np.ndarray:
    """
    Convierte imagen RGB (H, W, 3) a formato (1, H, W, 3) para inferencia.
    """
    return np.expand_dims(imagen, axis=0)
