from django.urls import include, path

from .dashboard_api_views import api_dashboard_summary

urlpatterns = [
    path("auth/", include("authtoken.api_urls")),
    path("cultivos/", include("cultivos.api_urls")),
    path("lotes/", include("lotes.api_urls")),
    path("metricas/", include("metricas.api_urls")),
    path("ubicaciones/", include("ubicaciones.api_urls")),
    path("repository/", include("repository.api_urls")),
    path("geolocation/", include("geolocation.api_urls")),
    path("dashboard/summary/", api_dashboard_summary, name="dashboard_summary"),
]
