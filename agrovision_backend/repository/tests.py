import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings

from cultivos.models import Cultivo
from metricas.models import Analisis, Metrica

from .models import ImagenCultivo, ImagenRepositorio, RepositorioImagen
from .providers.base import RepositoryProviderError
from .providers.cloudinary_provider import CloudinaryProvider

FAKE_RESULTADO_JSON = {
    "cantidad_frutos": {"valor": 8, "unidad": "unidades"},
    "frutos_maduros": {"valor": 3, "unidad": "unidades"},
    "estimacion_cosecha": {"valor": 0.054, "unidad": "kg"},
    "porcentaje_madurez": {"valor": 37.5, "unidad": "%"},
    "debug": {},
}


def _fake_process_images_ok(archivos, cultivo_id, lote_id=None, notas=""):
    return {
        "imagenes_procesadas": len(archivos),
        "resultado_json": FAKE_RESULTADO_JSON,
        "notas": notas,
        "modelo_usado": "maskrcnn_strawberry_best.pt",
    }


class RepositoryProcesamientoTests(TestCase):
    """TAREA 1: persistencia del flujo Cloudinary — asociación de imágenes al análisis."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ru1", password="pass12345")
        self.cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Fresas Repo", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        # self.imagenes son las ASOCIACIONES (ImagenCultivo) — es lo que la API
        # de procesamiento referencia por id (image_ids), no el asset global.
        self.imagenes = []
        for i in range(2):
            asset = ImagenRepositorio.objects.create(
                asset_id=f"asset-{i}", public_id=f"agrovision/img-{i}",
                secure_url=f"https://res.cloudinary.com/demo/image/upload/img-{i}.jpg",
            )
            self.imagenes.append(
                ImagenCultivo.objects.create(imagen=asset, cultivo=self.cultivo, usuario=self.user)
            )
        self.client.login(username="ru1", password="pass12345")

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_procesar_asocia_imagenes_al_analisis_y_marca_procesada(self, _mock_bytes, _mock_process):
        response = self.client.post(
            "/api/repository/images/process/",
            {"cultivo_id": self.cultivo.id, "image_ids": [i.id for i in self.imagenes]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "COMPLETADO")
        self.assertGreaterEqual(body["duracion_segundos"], 0)
        self.assertEqual(body["metrics"]["cantidad_frutos"], 8)

        # Una sola fila — Analisis.objects.get() falla con MultipleObjectsReturned
        # si el "procesando" inicial y el "procesado" final quedaran como dos filas.
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.origen, "repositorio")
        self.assertEqual(analisis.estado, "procesado")
        self.assertEqual(analisis.cantidad_frutos, 8)
        self.assertEqual(analisis.porcentaje_madurez, Decimal("37.50"))
        self.assertEqual(Metrica.objects.filter(cultivo=self.cultivo).count(), 4)

        for asociacion in self.imagenes:
            asociacion.refresh_from_db()
            self.assertEqual(asociacion.estado, "procesada")
            self.assertTrue(asociacion.procesada)
            self.assertEqual(asociacion.analisis_id, analisis.id)

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_analisis_queda_asociado_al_repositorio_de_origen(self, _mock_bytes, _mock_process):
        """Punto: Analisis.repositorio se toma del repositorio con el que se sincronizó la imagen."""
        repo = RepositorioImagen(
            usuario=self.user, nombre="Repo test", cloud_name="demo", api_key="k", carpeta_raiz="agrovision",
        )
        repo.set_api_secret("s")
        repo.save()
        for asociacion in self.imagenes:
            asociacion.imagen.repositorio = repo
            asociacion.imagen.save(update_fields=["repositorio"])

        response = self.client.post(
            "/api/repository/images/process/",
            {"cultivo_id": self.cultivo.id, "image_ids": [i.id for i in self.imagenes]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.repositorio_id, repo.id)

    @patch("repository.api_views.services.descargar_bytes", side_effect=Exception("timeout de red"))
    def test_error_de_descarga_marca_imagenes_y_analisis_como_error(self, _mock_bytes):
        response = self.client.post(
            "/api/repository/images/process/",
            {"cultivo_id": self.cultivo.id, "image_ids": [i.id for i in self.imagenes]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)

        # Una sola fila: el error actualiza la fila "procesando" ya creada,
        # no crea una segunda — evita historial duplicado por la misma corrida.
        self.assertEqual(Analisis.objects.filter(cultivo=self.cultivo).count(), 1)
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.estado, "error")
        self.assertIsNone(analisis.cantidad_frutos)
        # El detalle técnico de la excepción ("timeout de red") se registra en
        # el log del servidor, no en un campo visible para el usuario final.
        self.assertEqual(analisis.mensaje_error, "El procesamiento no pudo completarse.")

        for asociacion in self.imagenes:
            asociacion.refresh_from_db()
            self.assertEqual(asociacion.estado, "error")


class RepositoryProcesarTodoTests(TestCase):
    """
    Nuevo flujo: "Procesar imágenes pendientes" — procesa automáticamente
    TODAS las imágenes en estado disponible (pendiente) del cultivo, sin que
    el cliente elija cuáles ni envíe image_ids.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="pt1", password="pass12345")
        self.cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="Fresas Auto", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        self.client.login(username="pt1", password="pass12345")

    def _crear_imagen(self, cultivo=None, usuario=None, asociacion_overrides=None, **asset_overrides):
        """Crea un asset global + su asociación con `cultivo` (self.cultivo por defecto). Devuelve la asociación."""
        n = ImagenRepositorio.objects.count()
        base = dict(
            asset_id=f"asset-{n}",
            public_id=f"agrovision/img-{n}",
            secure_url=f"https://res.cloudinary.com/demo/image/upload/img-{n}.jpg",
        )
        base.update(asset_overrides)
        asset = ImagenRepositorio.objects.create(**base)
        return ImagenCultivo.objects.create(
            imagen=asset, cultivo=cultivo or self.cultivo, usuario=usuario or self.user,
            **(asociacion_overrides or {}),
        )

    def _procesar(self, **payload_overrides):
        payload = {"cultivo_id": self.cultivo.id}
        payload.update(payload_overrides)
        return self.client.post("/api/repository/process-all/", payload, content_type="application/json")

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_una_imagen_pendiente(self, _mock_bytes, _mock_process):
        """Punto 1: repositorio con una imagen pendiente."""
        self._crear_imagen()
        response = self._procesar()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "COMPLETADO")
        self.assertEqual(body["imagenes_procesadas"], 1)
        self.assertEqual(body["imagenes_con_error"], 0)
        self.assertEqual(body["metrics"]["cantidad_frutos"], 8)

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_varias_imagenes_consolida_sumando_no_promediando(self, _mock_bytes, _mock_process):
        """Punto 2 y sección 9: cantidad_frutos/frutos_maduros se suman; porcentaje se recalcula sobre los totales."""
        for _ in range(3):
            self._crear_imagen()
        response = self._procesar()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["imagenes_procesadas"], 3)
        self.assertEqual(body["metrics"]["cantidad_frutos"], 24)
        self.assertEqual(body["metrics"]["frutos_maduros"], 9)
        self.assertEqual(body["metrics"]["porcentaje_madurez"], 37.5)  # 9/24*100, no promedio de 37.5 tres veces
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.cantidad_frutos, 24)
        self.assertEqual(analisis.estado, "procesado")

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_mezcla_de_procesadas_y_pendientes_solo_toma_pendientes(self, _mock_bytes, mock_process):
        """Punto 3: no se reprocesan por defecto imágenes ya 'procesada'."""
        self._crear_imagen(asociacion_overrides={"estado": "procesada", "procesada": True})
        self._crear_imagen(asociacion_overrides={"estado": "disponible"})
        response = self._procesar()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["imagenes_procesadas"], 1)
        self.assertEqual(mock_process.call_count, 1)

    def test_ninguna_imagen_pendiente_no_ejecuta_el_modelo(self):
        """Punto 4: sin pendientes, no se llama al modelo y no se crea Analisis."""
        self._crear_imagen(asociacion_overrides={"estado": "procesada", "procesada": True})
        with patch("repository.api_views.process_images") as mock_process:
            response = self._procesar()
            mock_process.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SIN_PENDIENTES")
        self.assertEqual(Analisis.objects.filter(cultivo=self.cultivo).count(), 0)

    @patch("repository.api_views.services.descargar_bytes")
    def test_imagen_corrupta_no_detiene_las_demas(self, mock_bytes):
        """Puntos 5 y 6: una imagen falla, se marca error, las demás continúan."""
        asoc_mala = self._crear_imagen()
        asoc_buena = self._crear_imagen()

        def _descargar(url):
            if url == asoc_mala.imagen.secure_url:
                raise Exception("imagen corrupta")
            return b"contenido-fake"

        mock_bytes.side_effect = _descargar

        with patch("repository.api_views.process_images", side_effect=_fake_process_images_ok):
            response = self._procesar()

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "COMPLETADO_CON_ERRORES")
        self.assertEqual(body["imagenes_procesadas"], 1)
        self.assertEqual(body["imagenes_con_error"], 1)

        asoc_mala.refresh_from_db()
        asoc_buena.refresh_from_db()
        self.assertEqual(asoc_mala.estado, "error")
        self.assertEqual(asoc_buena.estado, "procesada")

        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.estado, "procesado_con_errores")

    def test_todas_las_imagenes_fallan_marca_analisis_error(self):
        """Error crítico total: ninguna imagen se procesó -> Analisis en error, no COMPLETADO."""
        self._crear_imagen()
        with patch("repository.api_views.services.descargar_bytes", side_effect=Exception("timeout de red")):
            response = self._procesar()
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["status"], "ERROR")
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.estado, "error")

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_asociacion_correcta_al_cultivo_y_repositorio(self, _mock_bytes, _mock_process):
        """Punto 7: el análisis y las imágenes quedan asociados al cultivo y al repositorio de origen."""
        repo = RepositorioImagen(
            usuario=self.user, nombre="R", cloud_name="demo", api_key="k", carpeta_raiz="agrovision",
        )
        repo.set_api_secret("s")
        repo.save()
        asociacion = self._crear_imagen(repositorio=repo)

        response = self._procesar()
        self.assertEqual(response.status_code, 201)
        analisis = Analisis.objects.get(cultivo=self.cultivo)
        self.assertEqual(analisis.repositorio_id, repo.id)
        asociacion.refresh_from_db()
        self.assertEqual(asociacion.analisis_id, analisis.id)

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_persistencia_de_metricas_en_postgres(self, _mock_bytes, _mock_process):
        """Punto 8: se crean las 4 Metrica (cantidad_frutos, frutos_maduros, cosecha, madurez)."""
        self._crear_imagen()
        self._procesar()
        self.assertEqual(Metrica.objects.filter(cultivo=self.cultivo).count(), 4)

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_historial_no_sobrescribe_analisis_anteriores(self, _mock_bytes, _mock_process):
        """Punto 9: cada ejecución crea un Analisis nuevo, no se sobrescribe el anterior."""
        self._crear_imagen()
        self._procesar()
        self._crear_imagen()
        self._procesar()
        self.assertEqual(Analisis.objects.filter(cultivo=self.cultivo).count(), 2)

    @patch("repository.api_views.process_images", side_effect=_fake_process_images_ok)
    @patch("repository.api_views.services.descargar_bytes", return_value=b"contenido-fake")
    def test_filtra_por_lote_cuando_se_especifica(self, _mock_bytes, mock_process):
        """lote_id opcional: solo procesa las pendientes de ese lote."""
        from lotes.models import Lote

        lote = Lote.objects.create(cultivo=self.cultivo, nombre="L1", area_lote=1)
        self._crear_imagen(asociacion_overrides={"lote": lote})
        self._crear_imagen()  # sin lote — no debe incluirse

        response = self._procesar(lote_id=lote.id)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["imagenes_procesadas"], 1)
        self.assertEqual(mock_process.call_count, 1)


FAKE_RESOURCE_1 = {
    "asset_id": "asset-a", "public_id": "agrovision/img-a",
    "secure_url": "https://res.cloudinary.com/demo/image/upload/img-a.jpg",
    "format": "jpg", "width": 100, "height": 100, "bytes": 1000,
    "asset_folder": "agrovision", "resource_type": "image", "created_at": "2024-01-01T12:00:00Z",
}
FAKE_RESOURCE_2 = {
    "asset_id": "asset-b", "public_id": "agrovision/img-b",
    "secure_url": "https://res.cloudinary.com/demo/image/upload/img-b.jpg",
    "format": "jpg", "width": 200, "height": 200, "bytes": 2000,
    "asset_folder": "agrovision", "resource_type": "image", "created_at": "2024-01-02T08:30:00Z",
}

# Sin fallback global: aísla estos tests de las credenciales reales que
# pueda haber en el .env de la máquina donde corren.
_SIN_FALLBACK_GLOBAL = override_settings(
    CLOUDINARY_CLOUD_NAME="", CLOUDINARY_API_KEY="", CLOUDINARY_API_SECRET="",
)


@_SIN_FALLBACK_GLOBAL
class RepositorioConfiguracionTests(TestCase):
    """TAREA 1: configuración de repositorio por usuario (modelo, cifrado, endpoints)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="cfg1", password="pass12345")
        self.client.login(username="cfg1", password="pass12345")

    def _payload(self, **overrides):
        base = {
            "nombre": "Mi Cloudinary",
            "proveedor": "CLOUDINARY",
            "cloud_name": "demo",
            "api_key": "123456789",
            "api_secret": "supersecreto",
            "carpeta_raiz": "agrovision",
        }
        base.update(overrides)
        return base

    def test_usuario_sin_repositorio_no_puede_sincronizar(self):
        """Punto 1: sin repositorio propio y sin fallback global, sync devuelve 400 claro."""
        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        response = self.client.post(
            "/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RepositorioImagen.objects.count(), 0)

    @patch.object(CloudinaryProvider, "list_resources", return_value=([FAKE_RESOURCE_1, FAKE_RESOURCE_2], None))
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    def test_configuracion_valida_se_activa_y_no_expone_secreto(self, _mock_test, _mock_list):
        """Punto 2: guarda, activa, y la respuesta nunca incluye el api_secret."""
        response = self.client.post(
            "/api/repository/config/", self._payload(), content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertNotIn("api_secret", body["repositorio"])
        self.assertNotIn("api_secret_cifrado", body["repositorio"])
        self.assertEqual(body["descubrimiento"]["cantidad_encontradas"], 2)

        config = RepositorioImagen.objects.get(usuario=self.user)
        self.assertTrue(config.activo)
        self.assertEqual(config.estado_conexion, "conectado")
        self.assertNotEqual(config.api_secret_cifrado, "supersecreto")
        self.assertEqual(config.get_api_secret(), "supersecreto")

    @patch.object(CloudinaryProvider, "test_connection", return_value=(False, "Credenciales inválidas."))
    def test_credenciales_invalidas_no_se_guardan(self, _mock_test):
        """Punto 3: si la prueba de conexión falla, no se persiste ninguna fila."""
        response = self.client.post(
            "/api/repository/config/", self._payload(), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RepositorioImagen.objects.count(), 0)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    def test_probar_conexion_no_persiste(self, _mock_test):
        """Punto 4: /config/test/ solo prueba, nunca guarda."""
        response = self.client.post(
            "/api/repository/config/test/", self._payload(), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(RepositorioImagen.objects.count(), 0)

    @patch.object(CloudinaryProvider, "list_resources")
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    def test_primera_sincronizacion_no_persiste_imagenes_sin_cultivo(self, _mock_test, mock_list):
        """Punto 5: la primera sincronización al configurar es de descubrimiento, no crea filas (no hay cultivo aún)."""
        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        response = self.client.post(
            "/api/repository/config/", self._payload(), content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ImagenRepositorio.objects.count(), 0)

    @patch.object(CloudinaryProvider, "list_resources")
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    def test_resincronizacion_no_duplica(self, _mock_test, mock_list):
        """Puntos 6 y 7: resincronizar actualiza en vez de duplicar (upsert por asset_id/public_id)."""
        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")

        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1, FAKE_RESOURCE_2], None)
        r1 = self.client.post("/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json")
        self.assertEqual(r1.json()["created_assets"], 2)
        self.assertEqual(r1.json()["associated"], 2)

        r2 = self.client.post("/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json")
        self.assertEqual(r2.json()["created_assets"], 0)
        self.assertEqual(r2.json()["updated_assets"], 2)
        self.assertEqual(r2.json()["associated"], 0)
        self.assertEqual(r2.json()["already_associated"], 2)
        self.assertEqual(ImagenRepositorio.objects.count(), 2)
        self.assertEqual(ImagenCultivo.objects.filter(cultivo=cultivo).count(), 2)

        config = RepositorioImagen.objects.get(usuario=self.user)
        self.assertIsNotNone(config.ultimo_sync)
        self.assertEqual(ImagenRepositorio.objects.first().repositorio_id, config.id)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources", return_value=([], None))
    def test_cambio_de_repositorio_desactiva_el_anterior(self, _mock_list, _mock_test):
        """Punto 8: crear un segundo repositorio desactiva el primero; activar vuelve a cambiarlo."""
        self.client.post("/api/repository/config/", self._payload(nombre="Repo A"), content_type="application/json")
        self.client.post(
            "/api/repository/config/", self._payload(nombre="Repo B", cloud_name="demo2"),
            content_type="application/json",
        )
        repo_a = RepositorioImagen.objects.get(nombre="Repo A")
        repo_b = RepositorioImagen.objects.get(nombre="Repo B")
        repo_a.refresh_from_db()
        self.assertFalse(repo_a.activo)
        self.assertTrue(repo_b.activo)

        response = self.client.post(f"/api/repository/config/{repo_a.id}/activate/")
        self.assertEqual(response.status_code, 200)
        repo_a.refresh_from_db()
        repo_b.refresh_from_db()
        self.assertTrue(repo_a.activo)
        self.assertFalse(repo_b.activo)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources", return_value=([], None))
    def test_usuario_no_puede_acceder_al_repositorio_de_otro(self, _mock_list, _mock_test):
        """Punto 9: aislamiento entre usuarios — 404, no 403 (no revela existencia)."""
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        repo = RepositorioImagen.objects.get(usuario=self.user)

        User.objects.create_user(username="cfg2", password="pass12345")
        other_client = Client()
        other_client.login(username="cfg2", password="pass12345")

        self.assertEqual(other_client.get(f"/api/repository/config/{repo.id}/").status_code, 404)
        self.assertEqual(other_client.post(f"/api/repository/config/{repo.id}/activate/").status_code, 404)
        self.assertEqual(other_client.post(f"/api/repository/config/{repo.id}/deactivate/").status_code, 404)
        self.assertEqual(other_client.post(f"/api/repository/config/{repo.id}/test/").status_code, 404)

    @patch.object(CloudinaryProvider, "list_resources", side_effect=RepositoryProviderError("timeout de red"))
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    def test_error_de_cloudinary_durante_sync_marca_fallido(self, _mock_test, _mock_list):
        """Punto 10: un error del proveedor durante sync no rompe con 500 y marca el repositorio."""
        # Configura sin descubrimiento (list_resources ya está mockeado para fallar).
        with patch.object(CloudinaryProvider, "list_resources", return_value=([], None)):
            self.client.post("/api/repository/config/", self._payload(), content_type="application/json")

        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        response = self.client.post(
            "/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 502)

        config = RepositorioImagen.objects.get(usuario=self.user)
        self.assertEqual(config.estado_conexion, "fallido")

    def test_listar_carpetas_sin_repositorio_configurado(self):
        """Sin repositorio propio ni fallback global: 400 con mensaje limpio, sin credenciales."""
        response = self.client.get("/api/repository/folders/")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertNotIn("secret", body["message"].lower())

    @patch.object(CloudinaryProvider, "list_folders", return_value=["agrovision", "fresas2", "mangos"])
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources", return_value=([], None))
    def test_listar_carpetas_devuelve_carpetas_reales_sin_tocar_env(self, _mock_list_res, _mock_test, _mock_folders):
        """Las carpetas nuevas en Cloudinary aparecen sin modificar CLOUDINARY_FOLDER ni el .env."""
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")

        response = self.client.get("/api/repository/folders/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["folders"], ["agrovision", "fresas2", "mangos"])

    @patch.object(CloudinaryProvider, "list_folders", side_effect=RepositoryProviderError("timeout de red"))
    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources", return_value=([], None))
    def test_listar_carpetas_error_no_expone_detalle_tecnico(self, _mock_list_res, _mock_test, _mock_folders):
        """Un error de Cloudinary al listar carpetas se traduce a un mensaje limpio, no la excepción cruda."""
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")

        response = self.client.get("/api/repository/folders/")
        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertNotIn("timeout de red", body["message"])

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_sync_con_carpeta_distinta_a_la_guardada(self, mock_list, _mock_test):
        """
        La carpeta enviada en el request tiene prioridad sobre carpeta_raiz ya
        guardada, y queda persistida para la próxima sincronización — sin tocar
        CLOUDINARY_FOLDER ni reiniciar el backend.
        """
        mock_list.return_value = ([], None)
        self.client.post(
            "/api/repository/config/", self._payload(carpeta_raiz="agrovision"), content_type="application/json",
        )
        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1], None)

        response = self.client.post(
            "/api/repository/sync/",
            {"cultivo_id": cultivo.id, "carpeta": "fresas2"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["folder"], "fresas2")
        self.assertEqual(body["total_cloudinary"], 1)
        self.assertEqual(body["created_assets"], 1)
        self.assertEqual(body["associated"], 1)

        config = RepositorioImagen.objects.get(usuario=self.user)
        self.assertEqual(config.carpeta_raiz, "fresas2")

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_sync_guarda_asset_folder_resource_type_y_fecha_cloudinary(self, mock_list, _mock_test):
        """Regresión: la sincronización debe persistir asset_folder/resource_type/fecha_creacion_cloudinary."""
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        self.client.post("/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json")

        imagen = ImagenRepositorio.objects.get(public_id="agrovision/img-a")
        self.assertEqual(imagen.asset_folder, "agrovision")
        self.assertEqual(imagen.resource_type, "image")
        self.assertIsNotNone(imagen.fecha_creacion_cloudinary)
        self.assertEqual(imagen.fecha_creacion_cloudinary.year, 2024)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_sync_sin_cultivo_solo_sincroniza_repositorio(self, mock_list, _mock_test):
        """Sin cultivo_id: se hace upsert del asset global, pero no se crea ninguna asociación."""
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")

        mock_list.return_value = ([FAKE_RESOURCE_1, FAKE_RESOURCE_2], None)
        response = self.client.post("/api/repository/sync/", {}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["created_assets"], 2)
        self.assertEqual(body["associated"], 0)
        self.assertEqual(
            body["message"],
            "Las imágenes fueron sincronizadas en el repositorio, pero no se asociaron a un cultivo porque no se seleccionó ninguno.",
        )
        self.assertEqual(ImagenRepositorio.objects.count(), 2)
        self.assertEqual(ImagenCultivo.objects.count(), 0)

    # ==================== Casos 1-4 pedidos: asociación muchos-a-muchos ====================

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_caso1_imagen_nueva_se_crea_y_asocia_al_cultivo(self, mock_list, _mock_test):
        """Caso 1: imagen nueva en Cloudinary + cultivo A -> crea asset y asociación, aparece en su galería."""
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        cultivo_a = Cultivo.objects.create(
            usuario=self.user, nombre="Cultivo A", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        response = self.client.post(
            "/api/repository/sync/", {"cultivo_id": cultivo_a.id}, content_type="application/json",
        )
        body = response.json()
        self.assertEqual(body["created_assets"], 1)
        self.assertEqual(body["associated"], 1)
        self.assertEqual(body["total_visible_for_crop"], 1)

        galeria = self.client.get(f"/api/repository/images/?cultivo_id={cultivo_a.id}")
        self.assertEqual(galeria.json()["count"], 1)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_caso2_misma_imagen_se_asocia_a_un_segundo_cultivo_sin_perder_el_primero(self, mock_list, _mock_test):
        """
        Caso 2: imagen ya asociada a Cultivo A; el usuario sincroniza la misma
        carpeta para Cultivo B -> no duplica el asset, crea una asociación
        nueva para B, y sigue apareciendo en A (no se reasigna ni se pierde).
        """
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        cultivo_a = Cultivo.objects.create(
            usuario=self.user, nombre="Cultivo A", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        cultivo_b = Cultivo.objects.create(
            usuario=self.user, nombre="Cultivo B", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1, FAKE_RESOURCE_2], None)
        self.client.post("/api/repository/sync/", {"cultivo_id": cultivo_a.id}, content_type="application/json")

        response = self.client.post(
            "/api/repository/sync/", {"cultivo_id": cultivo_b.id}, content_type="application/json",
        )
        body = response.json()
        self.assertEqual(body["created_assets"], 0)  # el asset ya existía — no se duplica
        self.assertEqual(body["updated_assets"], 2)
        self.assertEqual(body["associated"], 2)  # asociación nueva para B
        self.assertEqual(body["message"], "Sincronización completada correctamente. Las imágenes quedaron asociadas al cultivo seleccionado.")

        self.assertEqual(ImagenRepositorio.objects.count(), 2)  # sin duplicar assets

        galeria_a = self.client.get(f"/api/repository/images/?cultivo_id={cultivo_a.id}")
        galeria_b = self.client.get(f"/api/repository/images/?cultivo_id={cultivo_b.id}")
        self.assertEqual(galeria_a.json()["count"], 2)  # A conserva su asociación
        self.assertEqual(galeria_b.json()["count"], 2)  # B ahora también las ve

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_caso3_sincronizar_dos_veces_mismo_cultivo_no_duplica_la_asociacion(self, mock_list, _mock_test):
        """Caso 3: sincronizar dos veces el mismo cultivo no duplica la asociación; created_assets da 0 la 2da vez."""
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        cultivo = Cultivo.objects.create(
            usuario=self.user, nombre="C1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        r1 = self.client.post("/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json")
        self.assertEqual(r1.json()["created_assets"], 1)
        self.assertEqual(r1.json()["associated"], 1)

        r2 = self.client.post("/api/repository/sync/", {"cultivo_id": cultivo.id}, content_type="application/json")
        self.assertEqual(r2.json()["created_assets"], 0)
        self.assertEqual(r2.json()["associated"], 0)
        self.assertEqual(r2.json()["already_associated"], 1)
        self.assertEqual(
            r2.json()["message"], "Las imágenes ya estaban asociadas a este cultivo. No se crearon duplicados.",
        )
        self.assertEqual(ImagenCultivo.objects.filter(cultivo=cultivo).count(), 1)

    @patch.object(CloudinaryProvider, "test_connection", return_value=(True, "Conexión exitosa."))
    @patch.object(CloudinaryProvider, "list_resources")
    def test_caso4_usuario_nuevo_asocia_asset_ya_existente_de_otro_usuario(self, mock_list, _mock_test):
        """Caso 4: un usuario nuevo sincroniza un asset que ya registró otro usuario -> crea su propia asociación."""
        mock_list.return_value = ([], None)
        self.client.post("/api/repository/config/", self._payload(), content_type="application/json")
        cultivo_u1 = Cultivo.objects.create(
            usuario=self.user, nombre="Cultivo U1", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )
        mock_list.return_value = ([FAKE_RESOURCE_1], None)
        self.client.post("/api/repository/sync/", {"cultivo_id": cultivo_u1.id}, content_type="application/json")

        user2 = User.objects.create_user(username="cfg_otro", password="pass12345")
        client2 = Client()
        client2.login(username="cfg_otro", password="pass12345")
        client2.post(
            "/api/repository/config/", self._payload(cloud_name="demo-otro"), content_type="application/json",
        )
        cultivo_u2 = Cultivo.objects.create(
            usuario=user2, nombre="Cultivo U2", tipo_fruto="fresa", ubicacion="Test",
            area_sembrada=1, fecha_siembra=datetime.date(2025, 1, 1),
        )

        response = client2.post(
            "/api/repository/sync/", {"cultivo_id": cultivo_u2.id}, content_type="application/json",
        )
        body = response.json()
        self.assertEqual(body["created_assets"], 0)  # mismo asset global, no se duplica
        self.assertEqual(body["associated"], 1)  # asociación propia para user2/cultivo_u2

        self.assertEqual(ImagenRepositorio.objects.count(), 1)
        galeria_u2 = client2.get(f"/api/repository/images/?cultivo_id={cultivo_u2.id}")
        self.assertEqual(galeria_u2.json()["count"], 1)
        # La asociación original del primer usuario sigue intacta.
        self.assertEqual(ImagenCultivo.objects.filter(cultivo=cultivo_u1, usuario=self.user).count(), 1)
