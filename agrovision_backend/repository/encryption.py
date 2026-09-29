"""
Cifrado simétrico (Fernet) para el api_secret de cada RepositorioImagen.

La clave se deriva de settings.SECRET_KEY por defecto para no exigir una
variable de entorno nueva en instalaciones existentes. Se puede fijar una
clave dedicada con REPOSITORY_ENCRYPTION_KEY (recomendado en producción,
para poder rotar SECRET_KEY sin invalidar los secretos ya cifrados).
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class SecretDecryptionError(Exception):
    """El secreto guardado no se pudo descifrar (clave rotada o dato corrupto)."""


def _fernet_key() -> bytes:
    clave_configurada = getattr(settings, "REPOSITORY_ENCRYPTION_KEY", "")
    if clave_configurada:
        return clave_configurada.encode("utf-8")
    # Deriva una clave Fernet válida (32 bytes url-safe base64) desde SECRET_KEY.
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(valor_plano: str) -> str:
    """Cifra un valor de texto plano y devuelve el token (string) a guardar en BD."""
    fernet = Fernet(_fernet_key())
    return fernet.encrypt(valor_plano.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Descifra un token previamente generado por encrypt_secret()."""
    fernet = Fernet(_fernet_key())
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretDecryptionError(
            "No se pudo descifrar el secreto almacenado (clave de cifrado inválida o dato corrupto)."
        ) from exc
