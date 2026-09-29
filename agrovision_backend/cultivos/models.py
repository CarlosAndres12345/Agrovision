from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class Cultivo(models.Model):
	usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cultivos')
	nombre = models.CharField(max_length=200)
	tipo_fruto = models.CharField(max_length=100)
	ubicacion = models.CharField(max_length=255)
	latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
	longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
	area_sembrada = models.DecimalField(max_digits=10, decimal_places=2)
	fecha_siembra = models.DateField()
	descripcion = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.nombre} ({self.tipo_fruto})"
