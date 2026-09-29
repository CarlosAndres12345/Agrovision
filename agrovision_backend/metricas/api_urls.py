from django.urls import path

from . import api_views

app_name = "metricas_api"

urlpatterns = [
    # Métricas existentes
    path("", api_views.api_crear_metrica, name="crear"),
    path("procesar/", api_views.api_procesar_dataset, name="procesar"),
    path("cultivo/<int:cultivo_id>/", api_views.api_metricas_por_cultivo, name="lista_por_cultivo"),
    path("cultivo/<int:cultivo_id>/resumen/", api_views.api_resumen_metricas_por_cultivo, name="resumen_por_cultivo"),
    path("lote/<int:lote_id>/", api_views.api_metricas_por_lote, name="lista_por_lote"),

    # Análisis (fase intermedia)
    path("analisis/", api_views.api_lista_analisis, name="lista_analisis"),
    path("analisis/manual/", api_views.api_crear_analisis_manual, name="crear_analisis_manual"),
    path("analisis/<int:analisis_id>/", api_views.api_detalle_analisis, name="detalle_analisis"),
    path("analisis/lote/<int:lote_id>/ultimo/", api_views.api_ultimo_analisis_lote, name="ultimo_analisis_lote"),
    path("analisis/cultivo/<int:cultivo_id>/ultimo/", api_views.api_ultimo_analisis_cultivo, name="ultimo_analisis_cultivo"),
]