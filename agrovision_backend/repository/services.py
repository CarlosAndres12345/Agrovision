"""
Reexporta la descarga de bytes (única operación sin credenciales) y el error
común del módulo de proveedores, para no romper los call sites existentes.
La obtención del proveedor concreto (Cloudinary hoy) vive en
repository/providers/ — ver providers.get_provider_for_user().
"""

from .providers.base import RepositoryProviderError
from .providers.cloudinary_provider import EXTENSIONES_VALIDAS, descargar_bytes

# Alias retrocompatible: código y tests existentes importan CloudinaryServiceError.
CloudinaryServiceError = RepositoryProviderError

__all__ = ["RepositoryProviderError", "CloudinaryServiceError", "EXTENSIONES_VALIDAS", "descargar_bytes"]
