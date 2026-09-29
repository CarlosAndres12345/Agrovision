from django.urls import path

from . import api_views

app_name = "ubicaciones_api"

urlpatterns = [
    path("", api_views.api_crear_ubicacion, name="crear"),
    path("cultivo/<int:cultivo_id>/", api_views.api_ubicaciones_por_cultivo, name="por_cultivo"),
    path("lote/<int:lote_id>/", api_views.api_ubicaciones_por_lote, name="por_lote"),
]
