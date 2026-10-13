"""yuppie-siliconflow：硅基流动 API 客户端库（图像 / 模型列表）"""

from __future__ import annotations

from .account import AccountMixin
from .base import SiliconFlowError, _SiliconFlowBase
from .config import DEFAULT_IMAGE_MODEL, SiliconFlowConfig
from .files import download_file, save_binary_file
from .images import ASPECT_RATIOS, RESOLUTIONS, ImagesMixin, resolve_image_size

__version__ = "0.1.0"

__all__ = [
    "SiliconFlowClient",
    "SiliconFlowConfig",
    "SiliconFlowError",
    "RESOLUTIONS",
    "ASPECT_RATIOS",
    "DEFAULT_IMAGE_MODEL",
    "resolve_image_size",
    "download_file",
    "save_binary_file",
    "__version__",
]


class SiliconFlowClient(ImagesMixin, AccountMixin, _SiliconFlowBase):
    """硅基流动 API 异步客户端，聚合文生图与模型列表能力。"""

    @classmethod
    def from_env(cls) -> SiliconFlowClient:
        """从环境变量构造客户端。"""
        return cls(SiliconFlowConfig.from_env())
