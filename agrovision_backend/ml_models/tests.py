from unittest.mock import patch

from django.test import SimpleTestCase


class ResolverDeviceTests(SimpleTestCase):
    """
    Tarea 2, punto 8: "detectar dispositivo CPU/GPU". No hay GPU en esta
    máquina de desarrollo — se mockea torch.cuda.is_available() para poder
    probar la rama "hay GPU disponible" sin hardware real.
    """

    def _resolver(self, device_config: str, cuda_disponible: bool):
        with patch("ml_models.services.model_loader.DEVICE", device_config), \
             patch("torch.cuda.is_available", return_value=cuda_disponible):
            from ml_models.services.model_loader import _resolver_device
            return _resolver_device()

    def test_auto_sin_gpu_usa_cpu(self):
        self.assertEqual(str(self._resolver("auto", cuda_disponible=False)), "cpu")

    def test_auto_con_gpu_usa_cuda(self):
        self.assertEqual(str(self._resolver("auto", cuda_disponible=True)), "cuda")

    def test_cpu_forzado_usa_cpu_aunque_haya_gpu(self):
        self.assertEqual(str(self._resolver("cpu", cuda_disponible=True)), "cpu")

    def test_cuda_forzado_sin_gpu_cae_a_cpu(self):
        self.assertEqual(str(self._resolver("cuda", cuda_disponible=False)), "cpu")

    def test_cuda_forzado_con_gpu_usa_cuda(self):
        self.assertEqual(str(self._resolver("cuda", cuda_disponible=True)), "cuda")

    def test_valor_invalido_cae_a_auto(self):
        self.assertEqual(str(self._resolver("tpu", cuda_disponible=False)), "cpu")
