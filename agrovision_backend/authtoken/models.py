import secrets
from django.db import models
from django.contrib.auth.models import User


class Token(models.Model):
    """
    Token simple para autenticación de API.
    Usuario puede tener solo un token activo.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="auth_token")
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token({self.user.username})"

    @classmethod
    def generate_token(cls):
        """Genera token seguro y único."""
        while True:
            token = secrets.token_urlsafe(32)
            if not cls.objects.filter(token=token).exists():
                return token

    @classmethod
    def create_for_user(cls, user):
        """Crea o actualiza token para usuario."""
        token_str = cls.generate_token()
        token, created = cls.objects.update_or_create(
            user=user,
            defaults={"token": token_str}
        )
        return token

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
