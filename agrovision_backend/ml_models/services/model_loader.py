"""
AgroVision OS - Model Loader
Carga y gestiona el modelo Mask R-CNN (torchvision) para análisis de cultivos.
"""

from pathlib import Path
from typing import Optional

from ml_models.utils.config import CHECKPOINTS_DIR, DEFAULT_MODEL_PATH, DEVICE


class ModeloNoDisponibleError(Exception):
    """Se lanza cuando el modelo no está disponible."""
    pass


def _resolver_device():
    """
    Resuelve el torch.device real a usar: "auto" detecta CUDA y cae a CPU si
    no hay GPU disponible; "cuda"/"cpu" fuerzan explícitamente (con el mismo
    fallback si se pide "cuda" sin GPU presente).
    """
    import torch

    preferencia = DEVICE
    if preferencia not in ("auto", "cpu", "cuda"):
        preferencia = "auto"

    if preferencia == "auto":
        nombre = "cuda" if torch.cuda.is_available() else "cpu"
    elif preferencia == "cuda" and not torch.cuda.is_available():
        nombre = "cpu"
    else:
        nombre = preferencia

    return torch.device(nombre)


class ModelLoader:
    """
    Singleton para cargar el modelo una sola vez y reusarlo en inferencia.
    """

    _instance = None
    _model = None
    _class_map = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def cargar_modelo(self, ruta_modelo: Optional[Path] = None) -> None:
        """
        Carga el checkpoint real de Mask R-CNN (torchvision, ResNet-50 FPN)
        desde disco, lo mueve al device detectado (GPU si hay CUDA
        disponible, si no CPU) y lo deja en modo evaluación.

        Raises:
            ModeloNoDisponibleError: Si el archivo no existe o no se puede cargar.
        """
        if ruta_modelo is None:
            ruta_modelo = DEFAULT_MODEL_PATH

        ruta_modelo = Path(ruta_modelo)

        if not ruta_modelo.exists():
            disponibles = [
                f.name for f in CHECKPOINTS_DIR.glob("*") if f.is_file()
            ] if CHECKPOINTS_DIR.exists() else []
            raise ModeloNoDisponibleError(
                f"Modelo no encontrado en {ruta_modelo}. "
                f"Archivos disponibles en checkpoints/: {disponibles}"
            )

        import torch
        from torchvision.models.detection import maskrcnn_resnet50_fpn

        device = _resolver_device()

        try:
            checkpoint = torch.load(str(ruta_modelo), map_location=device, weights_only=False)
            state_dict = checkpoint["model_state_dict"]
            # Número de clases derivado del propio checkpoint (background + clases entrenadas).
            num_classes = state_dict["roi_heads.box_predictor.cls_score.weight"].shape[0]

            modelo = maskrcnn_resnet50_fpn(weights=None, weights_backbone=None, num_classes=num_classes)
            modelo.load_state_dict(state_dict)
            modelo.to(device)
            modelo.eval()
        except Exception as exc:
            raise ModeloNoDisponibleError(
                f"No se pudo cargar el checkpoint '{ruta_modelo.name}': {exc}"
            ) from exc

        self._model = modelo
        self._class_map = checkpoint.get("class_map", {})
        self._device = device

    @property
    def modelo(self):
        """Retorna el modelo de PyTorch cargado (torchvision MaskRCNN, modo eval)."""
        if self._model is None:
            self.cargar_modelo()
        return self._model

    @property
    def device(self):
        """torch.device donde vive el modelo cargado (cuda si hay GPU, si no cpu)."""
        if self._model is None:
            self.cargar_modelo()
        return self._device

    @property
    def class_map(self) -> dict:
        """Mapeo id de clase -> nombre, tal como quedó guardado en el checkpoint."""
        if self._model is None:
            self.cargar_modelo()
        return self._class_map or {}

    def esta_cargado(self) -> bool:
        """Indica si el modelo está en memoria."""
        return self._model is not None

    def descargar(self) -> None:
        """Libera el modelo de memoria."""
        self._model = None
        self._class_map = None
        self._device = None


def get_model_loader() -> ModelLoader:
    """Obtiene la instancia singleton del loader."""
    return ModelLoader()
