from django.urls import path

from . import api_views

app_name = "repository_api"

urlpatterns = [
    path("config/", api_views.api_lista_repositorios, name="lista_repositorios"),
    path("config/test/", api_views.api_probar_conexion, name="probar_conexion"),
    path("config/<int:repositorio_id>/", api_views.api_detalle_repositorio, name="detalle_repositorio"),
    path("config/<int:repositorio_id>/test/", api_views.api_probar_conexion_repositorio, name="probar_conexion_repositorio"),
    path("config/<int:repositorio_id>/activate/", api_views.api_activar_repositorio, name="activar_repositorio"),
    path("config/<int:repositorio_id>/deactivate/", api_views.api_desactivar_repositorio, name="desactivar_repositorio"),
    path("folders/", api_views.api_lista_carpetas, name="lista_carpetas"),
    path("sync/", api_views.api_sync, name="sync"),
    path("images/", api_views.api_lista_imagenes, name="lista_imagenes"),
    path("images/upload/", api_views.api_subir_imagen, name="subir_imagen"),
    path("images/process/", api_views.api_procesar_imagenes, name="procesar_imagenes"),
    path("process-all/", api_views.api_procesar_repositorio, name="procesar_repositorio"),
    path("images/<int:imagen_id>/", api_views.api_detalle_imagen, name="detalle_imagen"),
]
