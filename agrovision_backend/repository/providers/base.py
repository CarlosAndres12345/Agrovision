"""
Interfaz común de un proveedor de repositorio externo de imágenes (Strategy).
Cada proveedor concreto (Cloudinary hoy; otros después) implementa esta
interfaz sin que el resto del módulo (sync, procesamiento, vistas) conozca
sus detalles.
"""

from abc import ABC, abstractmethod


class RepositoryProviderError(Exception):
    """Error al comunicarse con el proveedor externo (conexión, credenciales, cuota, etc.)."""


class RepositoryProvider(ABC):
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Intenta autenticar contra el proveedor. Devuelve (ok, mensaje_legible)."""
        raise NotImplementedError

    @abstractmethod
    def list_resources(self, next_cursor: str | None = None, max_results: int = 100) -> tuple[list[dict], str | None]:
        """Lista una página de recursos de la carpeta configurada. Devuelve (recursos, next_cursor)."""
        raise NotImplementedError

    def list_all_resources(self) -> list[dict]:
        """Pagina automáticamente hasta traer todos los recursos de la carpeta configurada."""
        recursos: list[dict] = []
        cursor = None
        while True:
            pagina, cursor = self.list_resources(next_cursor=cursor)
            recursos.extend(pagina)
            if not cursor:
                break
        return recursos

    def list_folders(self) -> list[str]:
        """Lista las carpetas disponibles en la cuenta. Proveedores sin noción de carpetas devuelven []."""
        return []

    @abstractmethod
    def upload(self, archivo) -> dict:
        """Sube un archivo a la carpeta configurada y devuelve el recurso creado."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, public_id: str) -> None:
        raise NotImplementedError
