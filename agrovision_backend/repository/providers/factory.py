"""
Fábrica de proveedores (Strategy): decide qué RepositoryProvider usar para
un usuario dado, sin que las vistas ni los servicios conozcan Cloudinary
directamente.

Resolución:
1. Repositorio propio activo del usuario (RepositorioImagen.activo=True).
2. Si no tiene uno configurado, credenciales globales de settings (.env)
   como repositorio "por defecto" — mantiene compatible el comportamiento
   anterior a esta funcionalidad para quien no configure nada.
"""

from django.conf import settings

from .base import RepositoryProvider
from .cloudinary_provider import CloudinaryProvider


def _provider_from_config(config) -> RepositoryProvider:
    if config.proveedor == config.PROVEEDOR_CLOUDINARY:
        return CloudinaryProvider(
            cloud_name=config.cloud_name,
            api_key=config.api_key,
            api_secret=config.get_api_secret(),
            carpeta_raiz=config.carpeta_raiz,
        )
    raise ValueError(f"Proveedor no soportado: {config.proveedor}")


def _provider_from_global_settings() -> RepositoryProvider | None:
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
        return CloudinaryProvider(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            carpeta_raiz=settings.CLOUDINARY_FOLDER,
        )
    return None


def get_provider_for_user(usuario):
    """
    Devuelve (provider, config) para el usuario dado.
    - config es la instancia de RepositorioImagen usada, o None si se cayó
      al fallback global (para que el llamador sepa qué guardar en
      ImagenRepositorio.repositorio / Analisis.repositorio).
    - provider es None si el usuario no tiene repositorio propio activo Y
      tampoco hay credenciales globales configuradas.
    """
    from repository.models import RepositorioImagen

    config = RepositorioImagen.objects.filter(usuario=usuario, activo=True).first()
    if config is not None:
        return _provider_from_config(config), config

    return _provider_from_global_settings(), None
