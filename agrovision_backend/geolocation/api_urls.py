from django.urls import path

from . import api_views

app_name = "geolocation_api"

urlpatterns = [
    path("search/", api_views.api_geolocation_search, name="search"),
    path("reverse/", api_views.api_geolocation_reverse, name="reverse"),
]
