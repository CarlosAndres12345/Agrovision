"""
AgroVision OS - Configuración centralizada del módulo ML.
Rutas, thresholds, device y constantes del modelo.
"""

import os
from pathlib import Path

# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHECKPOINTS_DIR = BASE_DIR / "ml_models" / "checkpoints"
DEFAULT_MODEL_FILENAME = "maskrcnn_strawberry_best.pt"
DEFAULT_MODEL_PATH = CHECKPOINTS_DIR / DEFAULT_MODEL_FILENAME

# ============================================================
# Modelo
# ============================================================

MODEL_TYPE = "maskrcnn"

# "auto" detecta GPU (CUDA) en tiempo de carga y cae a CPU si no hay una
# disponible — ver ml_models/services/model_loader.py::_resolver_device().
# Se puede forzar con ML_DEVICE=cpu o ML_DEVICE=cuda en el entorno.
DEVICE = os.environ.get("ML_DEVICE", "auto")

# ============================================================
# Preprocesamiento de imágenes
# ============================================================

IMAGE_SIZE = 640  # Tamaño de entrada del modelo (px)
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# ============================================================
# Extensiones válidas
# ============================================================

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# ============================================================
# Métricas oficiales del sistema
# ============================================================

METRICAS_OFICIALES = {
    "cantidad_frutos": {
        "nombre": "Cantidad de frutos",
        "unidad": "unidades",
        "descripcion": "Número total de frutos detectados",
        "tipo_dato": "entero",
    },
    "frutos_maduros": {
        "nombre": "Frutos maduros",
        "unidad": "unidades",
        "descripcion": "Frutos que alcanzaron madurez óptima",
        "tipo_dato": "entero",
    },
    "estimacion_cosecha": {
        "nombre": "Estimación de cosecha",
        "unidad": "kg",
        "descripcion": "Peso estimado total de la cosecha",
        "tipo_dato": "float",
    },
    "porcentaje_madurez": {
        "nombre": "Porcentaje de madurez",
        "unidad": "%",
        "descripcion": "Proporción de frutos maduros sobre el total",
        "tipo_dato": "float",
    },
}


def extension_valida(nombre_archivo: str) -> bool:
    """Verifica si la extensión del archivo es válida para el modelo."""
    return Path(nombre_archivo).suffix.lower() in EXTENSIONES_VALIDAS


def ruta_checkpoints() -> Path:
    """Retorna la ruta absoluta a la carpeta de checkpoints."""
    return CHECKPOINTS_DIR


def ruta_modelo_default() -> Path:
    """Retorna la ruta absoluta al modelo por defecto."""
    return DEFAULT_MODEL_PATH


def modelo_disponible() -> bool:
    """Indica si el archivo de checkpoint existe físicamente."""
    return DEFAULT_MODEL_PATH.exists()
