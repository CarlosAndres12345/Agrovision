"""
Middleware y decoradores para validar tokens de autenticación.
"""
from functools import wraps
from django.http import JsonResponse
from .models import Token


def extract_token_from_header(request):
    """
    Extrae token del header Authorization: Bearer <token>
    Retorna (token_str, error_response) donde error_response es JsonResponse si hay error.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None, JsonResponse({"detail": "Autorización requerida."}, status=401)

    token_str = auth_header[7:]  # Quita "Bearer "
    if not token_str:
        return None, JsonResponse({"detail": "Token vacío."}, status=401)

    return token_str, None


def get_user_from_token(token_str):
    """
    Valida token y retorna (user, error_response).
    """
    try:
        token = Token.objects.select_related("user").get(token=token_str)
        return token.user, None
    except Token.DoesNotExist:
        return None, JsonResponse({"detail": "Token inválido o expirado."}, status=401)


def require_token(view_func):
    """
    Decorador que protege vista: requiere token válido en header.
    Pasa `request.user` con el usuario autenticado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token_str, error_response = extract_token_from_header(request)
        if error_response:
            return error_response

        user, error_response = get_user_from_token(token_str)
        if error_response:
            return error_response

        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper
