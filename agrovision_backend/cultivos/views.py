from django.shortcuts import get_object_or_404, render

from cultivos.models import Cultivo


def lista_cultivos(request):
	cultivos = Cultivo.objects.select_related('usuario').order_by('nombre')
	contexto = {
		'cultivos': cultivos,
	}
	return render(request, 'cultivos/lista.html', contexto)


def detalle_cultivo(request, cultivo_id):
	cultivo = get_object_or_404(Cultivo.objects.select_related('usuario'), pk=cultivo_id)
	contexto = {
		'cultivo': cultivo,
	}
	return render(request, 'cultivos/detalle.html', contexto)
