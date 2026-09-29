from django.contrib import admin
from .models import Cultivo


class CultivoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'tipo_fruto', 'usuario', 'area_sembrada', 'fecha_siembra', 'latitud', 'longitud', 'created_at')
	list_filter = ('tipo_fruto', 'fecha_siembra')
	search_fields = ('nombre', 'ubicacion', 'usuario__username')


admin.site.register(Cultivo, CultivoAdmin)
