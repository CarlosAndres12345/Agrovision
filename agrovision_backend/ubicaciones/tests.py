import datetime

from django.contrib.auth.models import User
from django.test import TestCase, Client

from cultivos.models import Cultivo
from lotes.models import Lote

from .models import Ubicacion


class UbicacionPersistenceTests(TestCase):
    """
    TAREA H, puntos 1, 5, 6, 8, 9, 10, 11, 12, 16: persistencia real de las
    3 fuentes de ubicación (dispositivo, búsqueda de dirección, mapa).
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="loc1", password="pass12345")
        self.otro_user = User.objects.create_user(username="loc2", password="pass12345")
        self.cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Fresas", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        self.lote = Lote.objects.create(cultivo=self.cultivo, nombre="Lote 1", area_lote=1)
        self.client.login(username="loc1", password="pass12345")

    def _payload(self, **overrides):
        base = {
            "cultivo_id": self.cultivo.id,
            "latitude": 3.4516,
            "longitude": -76.5320,
            "source": "DEVICE_GEOLOCATION",
            "accuracy_meters": 12.5,
        }
        base.update(overrides)
        return base

    def test_ubicacion_actual_del_dispositivo_persiste(self):
        """Punto 1: DEVICE_GEOLOCATION requiere y guarda accuracy_meters."""
        response = self.client.post("/api/ubicaciones/", self._payload(), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.source, "DEVICE_GEOLOCATION")
        self.assertIsNotNone(ubicacion.accuracy_meters)

    def test_seleccion_de_resultado_de_busqueda_persiste_direccion(self):
        """Punto 5 y 8: ADDRESS_SEARCH guarda address, accuracy_meters puede ser null."""
        response = self.client.post(
            "/api/ubicaciones/",
            self._payload(
                source="ADDRESS_SEARCH",
                address="Cali, Valle del Cauca, Colombia",
                accuracy_meters=None,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.source, "ADDRESS_SEARCH")
        self.assertEqual(ubicacion.address, "Cali, Valle del Cauca, Colombia")
        self.assertIsNone(ubicacion.accuracy_meters)

    def test_clic_en_mapa_persiste_sin_precision(self):
        """Punto 6 y 8: MAP_SELECTION no requiere accuracy_meters."""
        response = self.client.post(
            "/api/ubicaciones/",
            self._payload(source="MAP_SELECTION", address="Cerca de Carrera 1", accuracy_meters=None),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.source, "MAP_SELECTION")
        self.assertIsNone(ubicacion.accuracy_meters)

    def test_device_geolocation_sin_accuracy_es_rechazado(self):
        """No confiar en el cliente: DEVICE_GEOLOCATION sin precisión es inválido."""
        response = self.client.post(
            "/api/ubicaciones/",
            self._payload(accuracy_meters=None),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_source_invalido_es_rechazado(self):
        response = self.client.post(
            "/api/ubicaciones/",
            self._payload(source="MANUAL_INPUT"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_latitud_longitud_fuera_de_rango_son_rechazadas(self):
        self.assertEqual(
            self.client.post(
                "/api/ubicaciones/", self._payload(latitude=200), content_type="application/json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/ubicaciones/", self._payload(longitude=-200), content_type="application/json"
            ).status_code,
            400,
        )

    def test_direccion_demasiado_larga_es_rechazada(self):
        response = self.client.post(
            "/api/ubicaciones/",
            self._payload(source="ADDRESS_SEARCH", accuracy_meters=None, address="x" * 501),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_asociacion_con_cultivo(self):
        """Punto 11: cultivo obligatorio y correctamente asociado."""
        self.client.post("/api/ubicaciones/", self._payload(), content_type="application/json")
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(ubicacion.cultivo_id, self.cultivo.id)

    def test_asociacion_opcional_con_lote(self):
        """Punto 12: lote es opcional y debe pertenecer al cultivo indicado."""
        response = self.client.post(
            "/api/ubicaciones/", self._payload(lote_id=self.lote.id), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Ubicacion.objects.get().lote_id, self.lote.id)

        otro_cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Otro", tipo_fruto="mango", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        response_invalido = self.client.post(
            "/api/ubicaciones/",
            self._payload(cultivo_id=otro_cultivo.id, lote_id=self.lote.id),
            content_type="application/json",
        )
        self.assertEqual(response_invalido.status_code, 400)

    def test_permisos_usuario_no_puede_asociar_cultivo_ajeno(self):
        self.client.logout()
        self.client.login(username="loc2", password="pass12345")
        response = self.client.post("/api/ubicaciones/", self._payload(), content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_requiere_autenticacion(self):
        self.client.logout()
        response = self.client.post("/api/ubicaciones/", self._payload(), content_type="application/json")
        self.assertEqual(response.status_code, 401)
