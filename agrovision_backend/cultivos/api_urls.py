from django.urls import path

from . import api_views

app_name = "cultivos_api"

urlpatterns = [
    path("", api_views.api_lista_cultivos, name="lista"),
    path("<int:cultivo_id>/", api_views.api_detalle_cultivo, name="detalle"),
    path("<int:cultivo_id>/metricas/", api_views.api_metricas_cultivo, name="metricas"),
]
