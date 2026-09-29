from django.contrib.auth.models import User
from django.test import TestCase, Client

from ubicaciones.models import Ubicacion

from .models import Cultivo


class CultivoConUbicacionTests(TestCase):
    """
    Reorganización del módulo de ubicación: la ubicación ahora se confirma
    dentro del formulario de cultivo (creación y edición), no en una
    pantalla independiente.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="cu1", password="pass12345")
        self.client.login(username="cu1", password="pass12345")

    def _payload_cultivo(self, **overrides):
        base = {
            "nombre": "Fresas del Valle",
            "tipo_fruto": "fresa",
            "ubicacion": "Cali, Valle del Cauca",
            "area_sembrada": "2.5",
            "fecha_siembra": "2025-01-01",
        }
        base.update(overrides)
        return base

    def _payload_location(self, **overrides):
        base = {
            "latitude": 3.4516,
            "longitude": -76.5320,
            "address": "Cali, Valle del Cauca, Colombia",
            "source": "ADDRESS_SEARCH",
        }
        base.update(overrides)
        return base

    def test_creacion_con_ubicacion_actual_del_dispositivo(self):
        """Punto 1: creación con DEVICE_GEOLOCATION persiste cultivo + ubicación."""
        payload = self._payload_cultivo(
            location=self._payload_location(source="DEVICE_GEOLOCATION", accuracy_meters=15.2)
        )
        response = self.client.post("/api/cultivos/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        data = response.json()

        cultivo = Cultivo.objects.get(pk=data["id"])
        self.assertEqual(cultivo.latitud, self._round(3.4516))
        ubicacion = Ubicacion.objects.get(cultivo=cultivo)
        self.assertEqual(ubicacion.source, "DEVICE_GEOLOCATION")
        self.assertIsNotNone(ubicacion.accuracy_meters)
        self.assertEqual(data["location"]["source"], "DEVICE_GEOLOCATION")

    def test_creacion_mediante_busqueda_de_direccion(self):
        """Punto 2: ADDRESS_SEARCH guarda la dirección seleccionada."""
        payload = self._payload_cultivo(location=self._payload_location(source="ADDRESS_SEARCH"))
        response = self.client.post("/api/cultivos/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.address, "Cali, Valle del Cauca, Colombia")

    def test_creacion_mediante_seleccion_en_mapa(self):
        """Punto 3: MAP_SELECTION no requiere accuracy_meters."""
        payload = self._payload_cultivo(
            location=self._payload_location(source="MAP_SELECTION", address="Cerca de Carrera 1")
        )
        response = self.client.post("/api/cultivos/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.source, "MAP_SELECTION")
        self.assertIsNone(ubicacion.accuracy_meters)

    def test_cultivo_sin_ubicacion_es_valido(self):
        """Punto 6: la ubicación es opcional — el cultivo se crea sin ella."""
        response = self.client.post(
            "/api/cultivos/", self._payload_cultivo(), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Ubicacion.objects.count(), 0)
        self.assertIsNone(response.json()["location"])

    def test_ubicacion_invalida_no_deja_cultivo_incompleto(self):
        """
        Sección 5: transaccional — si la ubicación enviada es inválida, no
        debe quedar un cultivo a medias (sin su ubicación esperada).
        """
        payload = self._payload_cultivo(
            location=self._payload_location(source="DEVICE_GEOLOCATION", accuracy_meters=None)
        )
        response = self.client.post("/api/cultivos/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Cultivo.objects.count(), 0)
        self.assertEqual(Ubicacion.objects.count(), 0)

    def test_edicion_de_ubicacion_no_duplica_registro(self):
        """Punto 7 y sección 4: editar la ubicación actualiza, no duplica."""
        creacion = self.client.post(
            "/api/cultivos/",
            self._payload_cultivo(location=self._payload_location(source="ADDRESS_SEARCH")),
            content_type="application/json",
        )
        cultivo_id = creacion.json()["id"]

        edicion = self.client.patch(
            f"/api/cultivos/{cultivo_id}/",
            self._payload_cultivo(
                location=self._payload_location(
                    source="MAP_SELECTION", address="Otro punto", latitude=3.5, longitude=-76.6
                )
            ),
            content_type="application/json",
        )
        self.assertEqual(edicion.status_code, 200)
        self.assertEqual(Ubicacion.objects.filter(cultivo_id=cultivo_id).count(), 1)
        ubicacion = Ubicacion.objects.get(cultivo_id=cultivo_id)
        self.assertEqual(ubicacion.source, "MAP_SELECTION")
        self.assertEqual(ubicacion.address, "Otro punto")

    def test_persistencia_tras_recargar_el_detalle(self):
        """Punto 9: GET del cultivo devuelve la ubicación ya guardada."""
        creacion = self.client.post(
            "/api/cultivos/",
            self._payload_cultivo(location=self._payload_location()),
            content_type="application/json",
        )
        cultivo_id = creacion.json()["id"]

        detalle = self.client.get(f"/api/cultivos/{cultivo_id}/")
        self.assertEqual(detalle.status_code, 200)
        self.assertIsNotNone(detalle.json()["location"])
        self.assertEqual(detalle.json()["location"]["address"], "Cali, Valle del Cauca, Colombia")

    def test_listado_no_incluye_ubicacion_para_evitar_n_mas_1(self):
        """El listado de cultivos no debe hacer una consulta de ubicación por fila."""
        for i in range(3):
            self.client.post(
                "/api/cultivos/",
                self._payload_cultivo(nombre=f"C{i}", location=self._payload_location()),
                content_type="application/json",
            )
        response = self.client.get("/api/cultivos/")
        self.assertEqual(response.status_code, 200)
        for item in response.json()["results"]:
            self.assertNotIn("location", item)

    @staticmethod
    def _round(value):
        from decimal import Decimal
        return Decimal(str(value))
