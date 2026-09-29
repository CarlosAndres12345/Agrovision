from django.shortcuts import get_object_or_404, render

from cultivos.models import Cultivo

from .models import Lote


def lotes_por_cultivo(request, cultivo_id):
	cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
	lotes = cultivo.lotes.all().order_by('nombre')
	contexto = {
		'cultivo': cultivo,
		'lotes': lotes,
	}
	return render(request, 'lotes/lista.html', contexto)


def detalle_lote(request, lote_id):
	lote = get_object_or_404(Lote.objects.select_related('cultivo'), pk=lote_id)
	metricas = lote.metricas.all().order_by('-fecha_registro')
	contexto = {
		'lote': lote,
		'cultivo': lote.cultivo,
		'metricas': metricas,
	}
	return render(request, 'lotes/detalle.html', contexto)
