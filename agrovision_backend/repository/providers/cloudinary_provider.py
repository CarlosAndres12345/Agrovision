"""
Adapter de Cloudinary sobre RepositoryProvider. Las credenciales se pasan
explícitamente en cada llamada al SDK (cloud_name/api_key/api_secret como
kwargs) — el SDK las usa solo para esa llamada sin mutar ninguna
configuración global ni de otro usuario/hilo.
"""

import urllib.error
import urllib.request

import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader

from .base import RepositoryProvider, RepositoryProviderError

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class CloudinaryProvider(RepositoryProvider):
    def __init__(self, cloud_name: str, api_key: str, api_secret: str, carpeta_raiz: str = ""):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.carpeta_raiz = carpeta_raiz or ""

    def _credenciales(self) -> dict:
        return {"cloud_name": self.cloud_name, "api_key": self.api_key, "api_secret": self.api_secret}

    def test_connection(self) -> tuple[bool, str]:
        try:
            cloudinary.api.ping(**self._credenciales())
            return True, "Conexión exitosa."
        except cloudinary.exceptions.AuthorizationRequired:
            return False, "Credenciales inválidas: cloud name, API key o API secret incorrectos."
        except cloudinary.exceptions.Error as exc:
            return False, f"No se pudo conectar con Cloudinary: {exc}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return False, f"No se pudo conectar con Cloudinary (error de red): {exc}"

    def list_resources(self, next_cursor: str | None = None, max_results: int = 100) -> tuple[list[dict], str | None]:
        """
        Lista los recursos de `self.carpeta_raiz`. Usa `resources_by_asset_folder`
        (respeta las carpetas reales de la Media Library, incluida en cuentas con
        Dynamic Folder Mode) y cae a `resources` con `prefix` si ese método no
        está disponible para la cuenta — mismo resultado en cuentas antiguas.
        """
        carpeta = (self.carpeta_raiz or "").strip()

        if carpeta:
            params = {"max_results": max_results, **self._credenciales()}
            if next_cursor:
                params["next_cursor"] = next_cursor
            try:
                resultado = cloudinary.api.resources_by_asset_folder(carpeta, **params)
                return resultado.get("resources", []), resultado.get("next_cursor")
            except cloudinary.exceptions.AuthorizationRequired as exc:
                raise RepositoryProviderError("Credenciales de Cloudinary inválidas.") from exc
            except cloudinary.exceptions.NotFound:
                return [], None
            except cloudinary.exceptions.Error:
                pass  # cuenta sin soporte para asset_folder — sigue con el fallback por prefix
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise RepositoryProviderError(f"Error de red al consultar Cloudinary: {exc}") from exc

        params = {
            "type": "upload",
            "resource_type": "image",
            "prefix": carpeta,
            "max_results": max_results,
            **self._credenciales(),
        }
        if next_cursor:
            params["next_cursor"] = next_cursor

        try:
            resultado = cloudinary.api.resources(**params)
        except cloudinary.exceptions.AuthorizationRequired as exc:
            raise RepositoryProviderError("Credenciales de Cloudinary inválidas.") from exc
        except cloudinary.exceptions.Error as exc:
            raise RepositoryProviderError(f"No se pudo consultar Cloudinary: {exc}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RepositoryProviderError(f"Error de red al consultar Cloudinary: {exc}") from exc

        return resultado.get("resources", []), resultado.get("next_cursor")

    def list_folders(self) -> list[str]:
        """
        Devuelve, en orden, todas las rutas de carpeta disponibles en la cuenta
        (carpetas raíz + subcarpetas, recorridas recursivamente) — para que el
        usuario elija una desde la interfaz sin tocar el .env.
        """
        creds = self._credenciales()

        def _hijas(carpeta_path: str | None) -> list[dict]:
            resultado = cloudinary.api.subfolders(carpeta_path, **creds) if carpeta_path else cloudinary.api.root_folders(**creds)
            return resultado.get("folders", [])

        rutas: list[str] = []

        def _recorrer(carpeta_path: str | None):
            for carpeta in _hijas(carpeta_path):
                ruta = carpeta.get("path") or carpeta.get("name")
                if not ruta:
                    continue
                rutas.append(ruta)
                _recorrer(ruta)

        try:
            _recorrer(None)
        except cloudinary.exceptions.AuthorizationRequired as exc:
            raise RepositoryProviderError("Credenciales de Cloudinary inválidas.") from exc
        except cloudinary.exceptions.Error as exc:
            raise RepositoryProviderError(f"No se pudo consultar las carpetas de Cloudinary: {exc}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RepositoryProviderError(f"Error de red al consultar Cloudinary: {exc}") from exc

        return sorted(rutas)

    def upload(self, archivo) -> dict:
        try:
            return cloudinary.uploader.upload(
                archivo,
                folder=self.carpeta_raiz,
                resource_type="image",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                **self._credenciales(),
            )
        except cloudinary.exceptions.Error as exc:
            raise RepositoryProviderError(f"No se pudo subir la imagen a Cloudinary: {exc}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RepositoryProviderError(f"Error de red al subir la imagen: {exc}") from exc

    def delete(self, public_id: str) -> None:
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image", **self._credenciales())
        except cloudinary.exceptions.Error as exc:
            raise RepositoryProviderError(f"No se pudo eliminar la imagen en Cloudinary: {exc}") from exc


def descargar_bytes(secure_url: str) -> bytes:
    """
    Descarga el binario de una imagen ya alojada en Cloudinary. `secure_url`
    proviene siempre de nuestra propia base de datos (ImagenRepositorio.secure_url),
    nunca de un valor enviado por el cliente — no requiere credenciales (URL
    de entrega pública firmada por Cloudinary al momento de subir/listar).
    """
    try:
        with urllib.request.urlopen(secure_url, timeout=30) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RepositoryProviderError(f"No se pudo descargar la imagen desde Cloudinary: {exc}") from exc
