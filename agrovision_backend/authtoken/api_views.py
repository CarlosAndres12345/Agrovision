import json

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def _serialize_user(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@csrf_exempt
def api_login(request):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Response: { "user": {...} }

    Autentica al usuario y crea una sesión Django.
    Django responde con Set-Cookie: sessionid=<token> en el header.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return JsonResponse(
            {"detail": "Usuario y contraseña son requeridos."},
            status=400,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {"detail": "Usuario o contraseña incorrectos."},
            status=401,
        )

    django_login(request, user)  # Crea sesión → Set-Cookie: sessionid=...

    return JsonResponse({"user": _serialize_user(user)}, status=200)


@csrf_exempt
def api_logout(request):
    """
    POST /api/auth/logout/
    Invalida la sesión en base de datos y limpia la cookie de sesión.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido."}, status=405)

    django_logout(request)  # Elimina session de BD + expira cookie

    return JsonResponse({"detail": "Sesión cerrada."}, status=200)


def api_me(request):
    """
    GET /api/auth/me/
    Retorna el usuario autenticado si la sesión es válida.
    Requiere que el frontend envíe credentials: 'include' (cookie sessionid).
    """
    if request.method != "GET":
        return JsonResponse({"detail": "Método no permitido."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"detail": "No autenticado."}, status=401)

    return JsonResponse(_serialize_user(request.user), status=200)


@csrf_exempt
def api_register(request):
    """
    POST /api/auth/register/
    Body: { "username": "...", "email": "...", "password": "...", "password2": "..." }
    Response: { "user": {...} }

    Crea el usuario, lo persiste en PostgreSQL e inicia sesión automáticamente.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    password2 = data.get("password2", "").strip()

    if not username or not password:
        return JsonResponse(
            {"detail": "Usuario y contraseña son requeridos."},
            status=400,
        )

    if len(password) < 6:
        return JsonResponse(
            {"detail": "La contraseña debe tener al menos 6 caracteres."},
            status=400,
        )

    if password != password2:
        return JsonResponse(
            {"detail": "Las contraseñas no coinciden."},
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"detail": "El nombre de usuario ya está en uso."},
            status=400,
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    django_login(request, user)  # Inicia sesión inmediatamente tras el registro

    return JsonResponse({"user": _serialize_user(user)}, status=201)
