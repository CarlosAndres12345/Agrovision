from django.shortcuts import get_object_or_404, render

from cultivos.models import Cultivo


def metricas_por_cultivo(request, cultivo_id):
	cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
	metricas = cultivo.metricas.select_related('lote').order_by('-fecha_registro', '-created_at')
	contexto = {
		'cultivo': cultivo,
		'metricas': metricas,
	}
	return render(request, 'metricas/lista.html', contexto)
