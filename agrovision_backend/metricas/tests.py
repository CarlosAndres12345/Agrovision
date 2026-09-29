import datetime
import io
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client

from cultivos.models import Cultivo
from lotes.models import Lote
from ml_models.services.service import ProcesamientoError

from .models import Analisis, Metrica

FAKE_RESULTADO_JSON = {
    "cantidad_frutos": {"valor": 10, "unidad": "unidades"},
    "frutos_maduros": {"valor": 4, "unidad": "unidades"},
    "estimacion_cosecha": {"valor": 0.072, "unidad": "kg"},
    "porcentaje_madurez": {"valor": 40.0, "unidad": "%"},
    "debug": {"boxes_filtrados": [], "scores_filtrados": []},
}


def _fake_process_images_ok(archivos, cultivo_id, lote_id=None, notas=""):
    return {
        "cultivo_id": cultivo_id,
        "lote_id": lote_id,
        "imagenes_procesadas": len(archivos),
        "metricas": {},
        "resultado_json": FAKE_RESULTADO_JSON,
        "imagenes_nombres": [getattr(a, "name", "img.jpg") for a in archivos],
        "notas": notas,
        "modelo_usado": "maskrcnn_strawberry_best.pt",
    }


def _imagen_test() -> SimpleUploadedFile:
    return SimpleUploadedFile("fruta.jpg", b"contenido-no-es-una-imagen-real", content_type="image/jpeg")


class AnalisisPersistenceTests(TestCase):
    """TAREA 6, puntos 1-5, 12-14: persistencia real del procesamiento."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.otro_user = User.objects.create_user(username="u2", password="pass12345")
        self.cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Fresas", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        self.lote = Lote.objects.create(cultivo=self.cultivo, nombre="Lote 1", area_lote=1)
        self.client.login(username="u1", password="pass12345")

    @patch("metricas.api_views.process_images", side_effect=_fake_process_images_ok)
    def test_procesamiento_exitoso_crea_analisis_y_metricas(self, _mock):
        """Punto 1 y 2: procesamiento exitoso persiste Analisis + Metrica."""
        response = self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": self.cultivo.id, "imagenes": [_imagen_test()]},
        )
        self.assertEqual(response.status_code, 201)

        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.estado, "procesado")
        self.assertEqual(analisis.cantidad_frutos, 10)
        self.assertEqual(analisis.frutos_maduros, 4)
        self.assertEqual(analisis.porcentaje_madurez, Decimal("40.00"))
        self.assertEqual(Metrica.objects.filter(cultivo=self.cultivo).count(), 4)

    @patch("metricas.api_views.process_images", side_effect=_fake_process_images_ok)
    def test_analisis_asociado_al_cultivo(self, _mock):
        """Punto 3: cultivo obligatorio y correctamente asociado."""
        self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": self.cultivo.id, "imagenes": [_imagen_test()]},
        )
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.cultivo_id, self.cultivo.id)

    @patch("metricas.api_views.process_images", side_effect=_fake_process_images_ok)
    def test_asociacion_opcional_a_lote(self, _mock):
        """Punto 4: lote es opcional, y si se envía debe pertenecer al cultivo."""
        response = self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": self.cultivo.id, "lote_id": self.lote.id, "imagenes": [_imagen_test()]},
        )
        self.assertEqual(response.status_code, 201)
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.lote_id, self.lote.id)

        # Un lote de otro cultivo debe rechazarse.
        otro_cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Otro", tipo_fruto="mango", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        response_invalido = self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": otro_cultivo.id, "lote_id": self.lote.id, "imagenes": [_imagen_test()]},
        )
        self.assertEqual(response_invalido.status_code, 400)

    @patch("metricas.api_views.process_images", side_effect=_fake_process_images_ok)
    def test_historial_conservado_no_sobrescribe(self, _mock):
        """Punto 5: cada procesamiento crea una fila nueva, nunca se sobrescribe."""
        for _ in range(3):
            self.client.post(
                "/api/metricas/analisis/manual/",
                {"cultivo_id": self.cultivo.id, "imagenes": [_imagen_test()]},
            )
        self.assertEqual(Analisis.objects.filter(cultivo=self.cultivo).count(), 3)

    @patch("metricas.api_views.process_images", side_effect=ProcesamientoError("El modelo no está disponible."))
    def test_error_en_inferencia_no_guarda_metricas_falsas(self, _mock):
        """Punto 12 y 13: si falla la inferencia, se registra el error sin métricas inventadas."""
        response = self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": self.cultivo.id, "imagenes": [_imagen_test()]},
        )
        self.assertEqual(response.status_code, 400)

        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.estado, "error")
        self.assertIn("no está disponible", analisis.mensaje_error)
        self.assertIsNone(analisis.cantidad_frutos)
        self.assertIsNone(analisis.frutos_maduros)
        self.assertIsNone(analisis.porcentaje_madurez)
        self.assertEqual(Metrica.objects.filter(cultivo=self.cultivo).count(), 0)

    def test_permisos_usuario_no_puede_procesar_cultivo_ajeno(self):
        """Punto 14: un usuario no puede operar sobre el cultivo de otro."""
        self.client.logout()
        self.client.login(username="u2", password="pass12345")
        response = self.client.post(
            "/api/metricas/analisis/manual/",
            {"cultivo_id": self.cultivo.id, "imagenes": [_imagen_test()]},
        )
        self.assertEqual(response.status_code, 404)


class CultivoMetricasEndpointTests(TestCase):
    """TAREA 2 y TAREA 6, puntos 6, 7, 11, 14: GET /api/cultivos/{id}/metricas/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.otro_user = User.objects.create_user(username="u2", password="pass12345")
        self.cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Fresas", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        self.client.login(username="u1", password="pass12345")

    def test_cultivo_sin_metricas_devuelve_null_no_cero(self):
        """Punto 7: cultivo sin análisis -> null explícito, no ceros, HTTP 200."""
        response = self.client.get(f"/api/cultivos/{self.cultivo.id}/metricas/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["ultimo_analisis"])
        self.assertIsNone(data["resumen"])
        self.assertEqual(data["historial"], [])

    def test_cultivo_con_metricas_devuelve_ultimo_y_resumen(self):
        """Punto 6 y 11: refleja el último análisis completado tras procesar."""
        Analisis.objects.create(
            usuario=self.user, cultivo=self.cultivo, origen="manual", estado="procesado",
            cantidad_imagenes=1, cantidad_frutos=50, frutos_maduros=20,
            porcentaje_madurez=Decimal("40.00"), estimacion_cosecha=Decimal("0.360"),
        )
        segundo = Analisis.objects.create(
            usuario=self.user, cultivo=self.cultivo, origen="manual", estado="procesado",
            cantidad_imagenes=1, cantidad_frutos=120, frutos_maduros=72,
            porcentaje_madurez=Decimal("60.00"), estimacion_cosecha=Decimal("1.296"),
        )

        response = self.client.get(f"/api/cultivos/{self.cultivo.id}/metricas/")
        data = response.json()
        self.assertEqual(data["ultimo_analisis"]["id"], segundo.id)
        self.assertEqual(data["resumen"]["cantidad_frutos_ultimo"], 120)
        self.assertEqual(data["resumen"]["total_analisis"], 2)

    def test_permiso_cultivo_ajeno_devuelve_404(self):
        """Punto 14: no se puede ver el detalle de un cultivo ajeno."""
        self.client.logout()
        self.client.login(username="u2", password="pass12345")
        response = self.client.get(f"/api/cultivos/{self.cultivo.id}/metricas/")
        self.assertEqual(response.status_code, 404)


class DashboardSummaryTests(TestCase):
    """TAREA 4 y TAREA 6, puntos 8, 9, 10, 13, 15: GET /api/dashboard/summary/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.client.login(username="u1", password="pass12345")

    def test_dashboard_sin_datos(self):
        """Punto 8: sin análisis, ceros/null explícitos, nunca inventados."""
        response = self.client.get("/api/dashboard/summary/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cantidad_frutos"], 0)
        self.assertEqual(data["frutos_maduros"], 0)
        self.assertIsNone(data["porcentaje_madurez"])
        self.assertEqual(data["total_analisis"], 0)
        self.assertEqual(data["evolucion"], [])
        self.assertEqual(data["registros_recientes"], [])

    def test_dashboard_pondera_porcentaje_madurez_no_promedia_simple(self):
        """Punto 9 y 10: suma ponderada de frutos, no promedio de porcentajes."""
        c1 = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        c2 = Cultivo.objects.create(
            usuario=self.user, nombre="C2", tipo_fruto="mango", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        # c1: 100 frutos, 60% maduros (60 maduros). c2: 10 frutos, 10% maduros (1 maduro).
        # Promedio simple de porcentajes = 35%. Ponderado real = 61/110 = 55.45%.
        Analisis.objects.create(
            usuario=self.user, cultivo=c1, origen="manual", estado="procesado",
            cantidad_imagenes=1, cantidad_frutos=100, frutos_maduros=60,
            porcentaje_madurez=Decimal("60.00"), estimacion_cosecha=Decimal("1.080"),
        )
        Analisis.objects.create(
            usuario=self.user, cultivo=c2, origen="manual", estado="procesado",
            cantidad_imagenes=1, cantidad_frutos=10, frutos_maduros=1,
            porcentaje_madurez=Decimal("10.00"), estimacion_cosecha=Decimal("0.018"),
        )

        response = self.client.get("/api/dashboard/summary/")
        data = response.json()
        self.assertEqual(data["cantidad_frutos"], 110)
        self.assertEqual(data["frutos_maduros"], 61)
        self.assertNotAlmostEqual(data["porcentaje_madurez"], 35.0, places=1)
        self.assertAlmostEqual(data["porcentaje_madurez"], 55.45, places=1)

    def _crear_cultivos_con_analisis(self, cantidad: int):
        for i in range(cantidad):
            c = Cultivo.objects.create(
                usuario=self.user, nombre=f"C{i}", tipo_fruto="fresa", ubicacion="Test",
                area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
            )
            Analisis.objects.create(
                usuario=self.user, cultivo=c, origen="manual", estado="procesado",
                cantidad_imagenes=1, cantidad_frutos=10, frutos_maduros=5,
                porcentaje_madurez=Decimal("50.00"), estimacion_cosecha=Decimal("0.09"),
            )

    def test_dashboard_sin_consultas_duplicadas(self):
        """
        Punto 15: el número de consultas no debe crecer con la cantidad de
        cultivos (nada de una query por cultivo / N+1).
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        self._crear_cultivos_con_analisis(2)

        with CaptureQueriesContext(connection) as ctx_pocos:
            response = self.client.get("/api/dashboard/summary/")
        self.assertEqual(response.status_code, 200)
        consultas_con_2_cultivos = len(ctx_pocos.captured_queries)

        self._crear_cultivos_con_analisis(8)  # ahora 10 cultivos en total

        with CaptureQueriesContext(connection) as ctx_muchos:
            response = self.client.get("/api/dashboard/summary/")
        self.assertEqual(response.status_code, 200)
        consultas_con_10_cultivos = len(ctx_muchos.captured_queries)

        self.assertEqual(
            consultas_con_2_cultivos,
            consultas_con_10_cultivos,
            "La cantidad de consultas no debe depender de la cantidad de cultivos (N+1).",
        )
