from django.conf import settings
from django.db import models

from .encryption import decrypt_secret, encrypt_secret


class RepositorioImagen(models.Model):
    """
    Configuración de repositorio externo de imágenes de un usuario (Cloudinary
    hoy; el campo `proveedor` deja la puerta abierta a otros proveedores sin
    tocar el resto del módulo — ver repository/providers/).

    api_secret nunca se guarda en texto plano (ver repository/encryption.py)
    ni se serializa al frontend (ver _serialize_repositorio en api_views.py).
    """

    PROVEEDOR_CLOUDINARY = "CLOUDINARY"
    PROVEEDOR_CHOICES = [
        (PROVEEDOR_CLOUDINARY, "Cloudinary"),
    ]

    ESTADO_CONEXION_CHOICES = [
        ("sin_probar", "Sin probar"),
        ("conectado", "Conectado"),
        ("fallido", "Fallido"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="repositorios_imagen",
    )
    nombre = models.CharField(max_length=150)
    proveedor = models.CharField(max_length=20, choices=PROVEEDOR_CHOICES, default=PROVEEDOR_CLOUDINARY)

    cloud_name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    api_secret_cifrado = models.TextField()
    carpeta_raiz = models.CharField(max_length=255, blank=True)

    activo = models.BooleanField(default=False)
    estado_conexion = models.CharField(max_length=20, choices=ESTADO_CONEXION_CHOICES, default="sin_probar")
    ultimo_sync = models.DateTimeField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        constraints = [
            # A lo sumo un repositorio activo por usuario — evita ambigüedad
            # sobre cuál usar al sincronizar/procesar.
            models.UniqueConstraint(
                fields=["usuario"],
                condition=models.Q(activo=True),
                name="unico_repositorio_activo_por_usuario",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_proveedor_display()}) — {self.usuario}"

    def set_api_secret(self, valor_plano: str) -> None:
        self.api_secret_cifrado = encrypt_secret(valor_plano)

    def get_api_secret(self) -> str:
        return decrypt_secret(self.api_secret_cifrado)


class ImagenRepositorio(models.Model):
    """
    Asset global de Cloudinary (repositorio externo) — identificado únicamente
    por `public_id`. No sabe a qué cultivo(s) pertenece: esa relación vive en
    ImagenCultivo, porque una misma imagen puede sincronizarse y asociarse a
    más de un cultivo (incluso de usuarios distintos) sin duplicar el asset.
    El archivo binario vive únicamente en Cloudinary; PostgreSQL solo guarda
    metadatos.
    """

    # Identificadores estables de Cloudinary — evitan duplicados en la sincronización.
    asset_id = models.CharField(max_length=255, unique=True)
    public_id = models.CharField(max_length=500, unique=True)

    secure_url = models.URLField(max_length=1000)
    nombre_original = models.CharField(max_length=255, blank=True)
    formato = models.CharField(max_length=20, blank=True)
    ancho = models.PositiveIntegerField(null=True, blank=True)
    alto = models.PositiveIntegerField(null=True, blank=True)
    tamano_bytes = models.PositiveBigIntegerField(null=True, blank=True)

    # Carpeta real de Cloudinary (Dynamic Folder Mode) y tipo de recurso — se
    # guardan tal como los devuelve la Admin API, para no depender de parsear
    # el public_id (que ya no codifica la carpeta en cuentas Dynamic Folder).
    asset_folder = models.CharField(max_length=500, blank=True)
    resource_type = models.CharField(max_length=20, blank=True, default="image")
    fecha_creacion_cloudinary = models.DateTimeField(
        null=True, blank=True, help_text="created_at reportado por Cloudinary para este asset.",
    )

    repositorio = models.ForeignKey(
        "RepositorioImagen",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes",
        help_text="Repositorio con el que se descubrió este asset por primera vez (informativo).",
    )

    fecha_sincronizacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_sincronizacion"]

    def __str__(self):
        return self.nombre_original or self.public_id


class ImagenCultivo(models.Model):
    """
    Asociación entre un asset de Cloudinary (ImagenRepositorio) y un cultivo
    (y opcionalmente un lote) de un usuario. Es donde vive el estado de
    procesamiento de ESA asociación puntual — la misma imagen puede estar
    "procesada" para un cultivo y "disponible" (sin procesar todavía) para
    otro, sin que uno pise el historial del otro.
    """

    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("procesando", "Procesando"),
        ("procesada", "Procesada"),
        ("error", "Error"),
    ]

    imagen = models.ForeignKey(
        ImagenRepositorio,
        on_delete=models.CASCADE,
        related_name="asociaciones",
    )
    cultivo = models.ForeignKey(
        "cultivos.Cultivo",
        on_delete=models.CASCADE,
        related_name="imagenes_repositorio",
    )
    lote = models.ForeignKey(
        "lotes.Lote",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes_repositorio",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="imagenes_repositorio",
    )

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")
    procesada = models.BooleanField(default=False)
    analisis = models.ForeignKey(
        "metricas.Analisis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes",
    )
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)

    fecha_asociacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_asociacion"]
        constraints = [
            # Una imagen no se asocia dos veces al mismo cultivo/usuario. `lote`
            # queda fuera de la clave a propósito: es opcional (casi siempre
            # NULL) y en Postgres NULL nunca es igual a NULL en un constraint
            # único, así que incluirlo no evitaría duplicados en el caso común.
            models.UniqueConstraint(
                fields=["imagen", "cultivo", "usuario"],
                name="unica_asociacion_imagen_cultivo_usuario",
            ),
        ]

    def __str__(self):
        lote_part = f" / {self.lote.nombre}" if self.lote else ""
        return f"{self.cultivo.nombre}{lote_part} — {self.imagen}"
