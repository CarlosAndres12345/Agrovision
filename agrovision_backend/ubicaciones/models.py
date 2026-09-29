from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Ubicacion(models.Model):
    """
    Ubicación asociada a un cultivo (y opcionalmente a un lote), capturada
    por uno de tres métodos: geolocalización del dispositivo, búsqueda de
    dirección (Nominatim) o selección manual de un punto en el mapa.
    """

    DEVICE_GEOLOCATION = "DEVICE_GEOLOCATION"
    ADDRESS_SEARCH = "ADDRESS_SEARCH"
    MAP_SELECTION = "MAP_SELECTION"

    SOURCE_CHOICES = [
        (DEVICE_GEOLOCATION, "Ubicación del dispositivo"),
        (ADDRESS_SEARCH, "Búsqueda de dirección"),
        (MAP_SELECTION, "Selección en el mapa"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ubicaciones",
    )
    cultivo = models.ForeignKey(
        "cultivos.Cultivo",
        on_delete=models.CASCADE,
        related_name="ubicaciones",
    )
    lote = models.ForeignKey(
        "lotes.Lote",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ubicaciones",
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    address = models.CharField(max_length=500, blank=True)
    # Solo tiene sentido para DEVICE_GEOLOCATION — nulo para búsqueda de
    # dirección y selección manual, que no reportan precisión de GPS.
    accuracy_meters = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    captured_at = models.DateTimeField()
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self):
        lote_part = f" / {self.lote.nombre}" if self.lote else ""
        return f"{self.cultivo.nombre}{lote_part} — ({self.latitude}, {self.longitude})"
