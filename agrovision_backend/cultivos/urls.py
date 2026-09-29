from django.urls import path

from . import views

app_name = 'cultivos'

urlpatterns = [
    path('', views.lista_cultivos, name='lista'),
    path('<int:cultivo_id>/', views.detalle_cultivo, name='detalle'),
]