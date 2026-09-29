from django.urls import path

from . import views

app_name = 'metricas'

urlpatterns = [
    path('cultivo/<int:cultivo_id>/', views.metricas_por_cultivo, name='lista_por_cultivo'),
]