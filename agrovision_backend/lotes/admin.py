from django.contrib import admin
from .models import Lote


class LoteAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'cultivo', 'ancho', 'largo', 'area_lote', 'latitud', 'longitud', 'created_at')
	list_filter = ('cultivo',)
	search_fields = ('nombre', 'cultivo__nombre', 'descripcion')


admin.site.register(Lote, LoteAdmin)
