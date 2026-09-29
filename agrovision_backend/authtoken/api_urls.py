from django.urls import path
from . import api_views

urlpatterns = [
    path("login/", api_views.api_login, name="api_login"),
    path("logout/", api_views.api_logout, name="api_logout"),
    path("me/", api_views.api_me, name="api_me"),
    path("register/", api_views.api_register, name="api_register"),
]
