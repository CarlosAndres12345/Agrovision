from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Metrica(models.Model):
    cultivo = models.ForeignKey('cultivos.Cultivo', on_delete=models.CASCADE, related_name='metricas')
    lote = models.ForeignKey('lotes.Lote', on_delete=models.CASCADE, related_name='metricas', null=True, blank=True)

    TIPOS_RESULTADO = [
        ('cantidad_frutos', 'Cantidad de frutos'),
        ('frutos_maduros', 'Frutos maduros'),
        ('estimacion_cosecha', 'Estimación de cosecha'),
        ('porcentaje_madurez', 'Porcentaje de madurez'),
    ]

    # Mantengo max_length=100 para evitar riesgo de truncado en datos existentes.
    tipo_resultado = models.CharField(max_length=100, choices=TIPOS_RESULTADO)
    valor = models.DecimalField(max_digits=12, decimal_places=4)
    unidad = models.CharField(max_length=50, blank=True)
    fecha_registro = models.DateTimeField()
    descripcion = models.TextField(blank=True)
    fuente = models.CharField(max_length=100, default='modelo_vision')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        lote_part = f" - {self.lote.nombre}" if self.lote else ""
        unidad_part = f" {self.unidad}" if self.unidad else ""
        return f"{self.tipo_resultado}: {self.valor}{unidad_part} ({self.cultivo.nombre}{lote_part})"


class Analisis(models.Model):
    """
    Registro persistente de un procesamiento de imágenes (Mask R-CNN) sobre
    un cultivo y, opcionalmente, un lote. Cada procesamiento crea una fila
    nueva — nunca se sobrescribe uno anterior, por lo que esta tabla es el
    historial oficial de análisis.

    Orígenes: 'manual' (imágenes subidas directamente) o 'repositorio'
    (imágenes de Cloudinary, ya sincronizadas, seleccionadas por ID — ver app 'repository').
    """
    ORIGEN_CHOICES = [
        ('manual', 'Subida manual'),
        ('repositorio', 'Repositorio (Cloudinary)'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('procesado', 'Procesado'),
        ('procesado_con_errores', 'Procesado con errores'),
        ('error', 'Error'),
    ]

    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='analisis')
    cultivo = models.ForeignKey('cultivos.Cultivo', on_delete=models.CASCADE, related_name='analisis')
    lote = models.ForeignKey('lotes.Lote', on_delete=models.SET_NULL, null=True, blank=True, related_name='analisis')
    repositorio = models.ForeignKey(
        'repository.RepositorioImagen', on_delete=models.SET_NULL, null=True, blank=True, related_name='analisis',
    )
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default='pendiente')

    # Lista de URLs/data URLs de imágenes usadas en el análisis
    # [{"url": "data:image/jpeg;base64,...", "nombre": "foto.jpg"}] (origen manual)
    # [{"url": "https://res.cloudinary.com/...", "nombre": "foto.jpg"}] (origen repositorio)
    imagen_urls = models.JSONField(default=list, blank=True)
    cantidad_imagenes = models.PositiveIntegerField(default=0)

    # Resultado crudo del modelo (métricas + bloque debug)
    resultado_json = models.JSONField(default=dict, blank=True)

    # Columnas tipadas de las 4 métricas oficiales — solo se completan si
    # estado='procesado'. Quedan en null si el procesamiento falló o si no
    # hubo detecciones suficientes para calcular el porcentaje.
    cantidad_frutos = models.PositiveIntegerField(null=True, blank=True)
    frutos_maduros = models.PositiveIntegerField(null=True, blank=True)
    porcentaje_madurez = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    estimacion_cosecha = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # Se completa solo si estado='error'.
    mensaje_error = models.TextField(blank=True)

    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.lote_id and self.lote.cultivo_id != self.cultivo_id:
            raise ValidationError("El lote debe pertenecer al cultivo del análisis.")
        if (
            self.cantidad_frutos is not None
            and self.frutos_maduros is not None
            and self.frutos_maduros > self.cantidad_frutos
        ):
            raise ValidationError("frutos_maduros no puede superar cantidad_frutos.")

    def __str__(self):
        lote_part = f" / {self.lote.nombre}" if self.lote else ""
        return f"{self.cultivo.nombre}{lote_part} — {self.origen} ({self.estado})"


# Alias para compatibilidad con importaciones existentes
ProcesamientoAnalisis = Analisis