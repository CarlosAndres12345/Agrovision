import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client

from . import services
from .services import GeocodingServiceError

FAKE_SEARCH_RESPONSE = [
    {
        "lat": "3.4516",
        "lon": "-76.5320",
        "display_name": "Cali, Valle del Cauca, Colombia",
        "address": {"city": "Cali", "state": "Valle del Cauca", "country": "Colombia"},
    }
]

FAKE_REVERSE_RESPONSE = {
    "display_name": "Carrera 1, Cali, Valle del Cauca, Colombia",
    "address": {"road": "Carrera 1", "city": "Cali"},
}


class GeolocationEndpointTests(TestCase):
    """TAREA H, puntos 2, 3, 4, 7, 13: endpoints de búsqueda y reversa."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username="geo1", password="pass12345")
        self.client.login(username="geo1", password="pass12345")

    @patch("geolocation.services._get_json", return_value=FAKE_SEARCH_RESPONSE)
    def test_busqueda_con_resultados(self, _mock):
        """Punto 2: búsqueda con resultados, máximo 5, con dirección completa."""
        response = self.client.get("/api/geolocation/search/?q=Cali")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertIn("Cali", data["results"][0]["display_name"])

    @patch("geolocation.services._get_json", return_value=[])
    def test_busqueda_sin_resultados(self, _mock):
        """Punto 3: búsqueda sin resultados devuelve lista vacía, no error."""
        response = self.client.get("/api/geolocation/search/?q=xyzxyzxyz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_busqueda_menos_de_3_caracteres_rechazada(self):
        """Punto 4: el backend exige mínimo 3 caracteres (no confía en el frontend)."""
        response = self.client.get("/api/geolocation/search/?q=ca")
        self.assertEqual(response.status_code, 400)

    @patch("geolocation.services._get_json", return_value=FAKE_REVERSE_RESPONSE)
    def test_geocodificacion_inversa_exitosa(self, _mock):
        """Punto 7: geocodificación inversa de un punto seleccionado."""
        response = self.client.get("/api/geolocation/reverse/?lat=3.4516&lon=-76.5320")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Carrera 1", response.json()["result"]["display_name"])

    @patch("geolocation.services._get_json", side_effect=GeocodingServiceError("timeout"))
    def test_errores_de_nominatim_devuelven_502(self, _mock):
        """Punto 13: errores del proveedor externo se manejan, no revientan la vista."""
        response = self.client.get("/api/geolocation/search/?q=Bogota")
        self.assertEqual(response.status_code, 502)

    def test_requiere_autenticacion(self):
        self.client.logout()
        response = self.client.get("/api/geolocation/search/?q=Cali")
        self.assertEqual(response.status_code, 401)


class GeolocationCacheYThrottleTests(TestCase):
    """TAREA H, puntos 14 y 15: límite de solicitudes y caché."""

    def setUp(self):
        cache.clear()
        services._last_request_at = 0.0

    @patch("geolocation.services._get_json", return_value=FAKE_SEARCH_RESPONSE)
    def test_cache_evita_repetir_la_misma_consulta(self, mock_get_json):
        """Punto 15: la segunda búsqueda idéntica no vuelve a llamar al proveedor."""
        services.buscar_direccion("Cali")
        services.buscar_direccion("Cali")
        self.assertEqual(mock_get_json.call_count, 1)

    @patch("time.sleep")
    def test_throttle_espera_minimo_1_segundo_entre_solicitudes(self, mock_sleep):
        """Punto 14: como máximo 1 solicitud por segundo al proveedor externo."""
        services._last_request_at = 0.0
        services._throttle()  # primera llamada, sin espera (han pasado "años" desde epoch=0)
        mock_sleep.reset_mock()

        services._throttle()  # inmediatamente después: debe esperar ~1s
        self.assertTrue(mock_sleep.called)
        espera = mock_sleep.call_args[0][0]
        self.assertGreater(espera, 0)
        self.assertLessEqual(espera, services.MIN_SECONDS_BETWEEN_REQUESTS)
