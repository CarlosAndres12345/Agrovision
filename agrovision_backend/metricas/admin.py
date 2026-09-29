from django.contrib import admin
from .models import Metrica


class MetricaAdmin(admin.ModelAdmin):
	list_display = ('tipo_resultado', 'valor', 'unidad', 'cultivo', 'lote', 'fecha_registro', 'created_at')
	list_filter = ('tipo_resultado', 'fecha_registro', 'fuente')
	search_fields = ('tipo_resultado', 'cultivo__nombre', 'lote__nombre')


admin.site.register(Metrica, MetricaAdmin)
