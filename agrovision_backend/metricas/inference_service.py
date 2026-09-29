"""
AgroVision OS - Inference Service (Wrapper)
Mantiene compatibilidad con el código existente (metricas/api_views.py)
importando desde el módulo ml_models reorganizado.
"""

from ml_models.services.inference import InferenceError, procesar_imagenes

__all__ = ["procesar_imagenes", "InferenceError"]
