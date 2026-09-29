"""
AgroVision OS - Metrics
Extrae y formatea métricas agrícolas desde los resultados del modelo.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MetricaAgricola:
    """Representa una métrica agrícola individual."""
    tipo: str
    valor: float
    unidad: str
    descripcion: Optional[str] = None


# Definiciones de las 4 métricas oficiales del sistema
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

# Peso promedio por fruto (gramos) alineado al notebook mejorado.
# Se usa para: estimacion_cosecha = (frutos_maduros * AVG_WEIGHT_PER_FRUIT_G) / 1000
AVG_WEIGHT_PER_FRUIT_G = 18.0

# Umbral de score para considerar válida una detección.
SCORE_THRESHOLD = 0.35

# Umbrales de madurez por color, tomados del config embebido en el
# checkpoint de entrenamiento (maskrcnn_strawberry_best.pt). El checkpoint
# no guarda la fórmula original, solo estos dos valores — la heurística de
# "rojo dominante" en ml_models/services/inference.py es una reconstrucción
# razonable, no una copia verificada del notebook de entrenamiento.
RIPE_RED_RATIO_THRESHOLD = 0.18
RIPE_MEAN_RED_MIN = 100.0


def validar_metrica(tipo: str, valor: float) -> MetricaAgricola:
    """
    Valida y retorna una métrica agrícola.

    Args:
        tipo: Clave de la métrica (cantidad_frutos, frutos_maduros, etc.)
        valor: Valor numérico de la métrica.

    Returns:
        MetricaAgricola validada.

    Raises:
        ValueError: Si el tipo no es reconocido o el valor es inválido.
    """
    if tipo not in METRICAS_OFICIALES:
        raise ValueError(
            f"Tipo de métrica desconocido: '{tipo}'. "
            f"Válidos: {list(METRICAS_OFICIALES.keys())}"
        )

    definicion = METRICAS_OFICIALES[tipo]
    valor_float = float(valor)

    if definicion["tipo_dato"] == "entero":
        valor_float = round(valor_float)
        if valor_float < 0:
            raise ValueError(f"La métrica '{tipo}' no puede ser negativa.")

    return MetricaAgricola(
        tipo=tipo,
        valor=valor_float,
        unidad=definicion["unidad"],
        descripcion=definicion["descripcion"],
    )


def formatear_para_respuesta(metricas: Dict[str, dict]) -> dict:
    """
    Formatea métricas para enviar al frontend.

    Args:
        metricas: Diccionario con métricas crudas del modelo.

    Returns:
        Diccionario listo para JSON response.
    """
    resultado = {}
    for tipo, datos in metricas.items():
        if tipo in METRICAS_OFICIALES:
            resultado[tipo] = {
                "valor": datos["valor"],
                "unidad": datos["unidad"],
                "nombre": METRICAS_OFICIALES[tipo]["nombre"],
            }
    return resultado


def calcular_resumen_cultivo(analisis_por_lote: list) -> dict:
    """
    Agrega métricas de múltiples lotes para dar resumen del cultivo.

    Args:
        analisis_por_lote: Lista de dicts con métricas por lote.

    Returns:
        Resumen agregado del cultivo.
    """
    if not analisis_por_lote:
        return {clave: None for clave in METRICAS_OFICIALES}

    resumen = {clave: [] for clave in METRICAS_OFICIALES}

    for analisis in analisis_por_lote:
        metricas = analisis.get("resultado_json", {})
        for clave in METRICAS_OFICIALES:
            if clave in metricas:
                resumen[clave].append(metricas[clave]["valor"])

    resultado = {}
    for clave, valores in resumen.items():
        if valores:
            resultado[clave] = {
                "valor": sum(valores) / len(valores),
                "unidad": METRICAS_OFICIALES[clave]["unidad"],
                "muestras": len(valores),
            }
        else:
            resultado[clave] = None

    return resultado
