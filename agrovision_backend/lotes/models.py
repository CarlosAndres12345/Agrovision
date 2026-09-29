from decimal import Decimal, ROUND_HALF_UP

from django.db import models

from cultivos.models import Cultivo


class Lote(models.Model):
	cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='lotes')
	nombre = models.CharField(max_length=200)
	ancho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	largo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	area_lote = models.DecimalField(max_digits=10, decimal_places=2)
	latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
	longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
	descripcion = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		if self.ancho is not None and self.largo is not None:
			self.area_lote = (self.ancho * self.largo).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.nombre} - {self.cultivo.nombre}"
