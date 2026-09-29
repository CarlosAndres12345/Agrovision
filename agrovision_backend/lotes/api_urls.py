from django.urls import path

from . import api_views

app_name = "lotes_api"

urlpatterns = [
    path("", api_views.api_lista_lotes, name="lista"),
    path("<int:lote_id>/", api_views.api_detalle_lote, name="detalle"),
    path("cultivo/<int:cultivo_id>/", api_views.api_lotes_por_cultivo, name="lista_por_cultivo"),
]
