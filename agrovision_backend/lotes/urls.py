from django.urls import path

from . import views

app_name = 'lotes'

urlpatterns = [
    path('cultivo/<int:cultivo_id>/', views.lotes_por_cultivo, name='lista_por_cultivo'),
    path('<int:lote_id>/', views.detalle_lote, name='detalle'),
]