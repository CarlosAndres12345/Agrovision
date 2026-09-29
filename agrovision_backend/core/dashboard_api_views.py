"""
Resumen general del dashboard ("Inicio") — agrega datos reales desde
PostgreSQL. No hay valores fijos: si no hay análisis, los indicadores
quedan en 0/null explícitos, nunca inventados.
"""

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone

from metricas.models import Analisis

DIAS_EVOLUCION = 30

# Un procesamiento con errores parciales (algunas imágenes fallaron, otras no)
# igual generó métricas reales sobre las que sí terminaron — cuenta para el
# resumen igual que un procesamiento sin errores.
_ESTADOS_CON_RESULTADO = ["procesado", "procesado_con_errores"]


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"detail": message}, status=status)


def api_dashboard_summary(request):
    """
    GET /api/dashboard/summary/

    Política de cálculo (documentada, no promedia porcentajes simples):
    - cantidad_frutos / frutos_maduros / estimacion_cosecha: suma del ÚLTIMO
      análisis COMPLETADO de cada cultivo del usuario (una fila por cultivo,
      vía DISTINCT ON — una sola consulta, sin N+1).
    - porcentaje_madurez: total_frutos_maduros / total_frutos * 100.
      Si total_frutos es 0, se devuelve null (no 0%).
    - evolucion: análisis completados de los últimos 30 días, agrupados por
      fecha, orden cronológico.
    - registros_recientes: últimos análisis (cualquier estado) del usuario.
    """
    if not request.user.is_authenticated:
        return _json_error("Autenticación requerida.", status=401)

    usuario = request.user

    ultimos_por_cultivo = list(
        Analisis.objects
        .filter(cultivo__usuario=usuario, estado__in=_ESTADOS_CON_RESULTADO)
        .order_by("cultivo_id", "-created_at")
        .distinct("cultivo_id")
    )

    total_frutos = sum((a.cantidad_frutos or 0) for a in ultimos_por_cultivo)
    total_maduros = sum((a.frutos_maduros or 0) for a in ultimos_por_cultivo)
    total_cosecha = sum((a.estimacion_cosecha or 0) for a in ultimos_por_cultivo)
    porcentaje_madurez = round((total_maduros / total_frutos) * 100.0, 2) if total_frutos > 0 else None

    total_analisis = Analisis.objects.filter(cultivo__usuario=usuario).count()

    desde = timezone.now() - timezone.timedelta(days=DIAS_EVOLUCION)
    evolucion_qs = (
        Analisis.objects
        .filter(cultivo__usuario=usuario, estado__in=_ESTADOS_CON_RESULTADO, created_at__gte=desde)
        .annotate(fecha=TruncDate("created_at"))
        .values("fecha")
        .annotate(cantidad_frutos=Sum("cantidad_frutos"), frutos_maduros=Sum("frutos_maduros"))
        .order_by("fecha")
    )
    evolucion = [
        {
            "fecha": e["fecha"].isoformat(),
            "cantidad_frutos": e["cantidad_frutos"] or 0,
            "frutos_maduros": e["frutos_maduros"] or 0,
        }
        for e in evolucion_qs
    ]

    recientes_qs = (
        Analisis.objects
        .filter(cultivo__usuario=usuario)
        .select_related("cultivo", "lote")
        .order_by("-created_at")[:10]
    )
    registros_recientes = [
        {
            "id": a.id,
            "cultivo": a.cultivo.nombre,
            "cultivo_id": a.cultivo_id,
            "lote": a.lote.nombre if a.lote else None,
            "lote_id": a.lote_id,
            "estado": a.estado,
            "fecha": a.created_at.isoformat(),
        }
        for a in recientes_qs
    ]

    return JsonResponse(
        {
            "cantidad_frutos": total_frutos,
            "frutos_maduros": total_maduros,
            "estimacion_cosecha": float(total_cosecha),
            "porcentaje_madurez": porcentaje_madurez,
            "total_analisis": total_analisis,
            "evolucion": evolucion,
            "registros_recientes": registros_recientes,
        },
        status=200,
    )
