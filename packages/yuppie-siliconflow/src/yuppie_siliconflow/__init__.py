"""yuppie-siliconflow：硅基流动 API 客户端库（文生图 / 图生图）"""

from __future__ import annotations

from .base import SiliconFlowError, _SiliconFlowBase
from .config import DEFAULT_IMAGE_MODEL, SiliconFlowConfig
from .files import download_file, fetch_bytes, guess_image_format, save_binary_file
from .images import (
    ASPECT_RATIOS,
    MODEL_ASPECT_SIZES,
    RESOLUTIONS,
    ImagesMixin,
    resolve_image_size,
)

__version__ = "0.1.0"

__all__ = [
    "SiliconFlowClient",
    "SiliconFlowConfig",
    "SiliconFlowError",
    "RESOLUTIONS",
    "ASPECT_RATIOS",
    "MODEL_ASPECT_SIZES",
    "DEFAULT_IMAGE_MODEL",
    "resolve_image_size",
    "download_file",
    "save_binary_file",
    "fetch_bytes",
    "guess_image_format",
    "__version__",
]


class SiliconFlowClient(ImagesMixin, _SiliconFlowBase):
    """硅基流动 API 异步客户端，聚合文生图与图生图能力。"""

    @classmethod
    def from_env(cls) -> SiliconFlowClient:
        """从环境变量构造客户端。"""
        return cls(SiliconFlowConfig.from_env())
