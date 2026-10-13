"""yuppie-siliconflow：硅基流动 API 客户端库（图像 / 视频 / 语音 / 账户）"""

from __future__ import annotations

from .account import AccountMixin
from .audio import SPEECH_MODELS, AudioMixin
from .base import SiliconFlowError, _SiliconFlowBase
from .config import DEFAULT_IMAGE_MODEL, SiliconFlowConfig
from .files import download_file, save_binary_file
from .images import ASPECT_RATIOS, RESOLUTIONS, ImagesMixin, resolve_image_size
from .videos import VIDEO_SIZES, VideosMixin

__version__ = "0.1.0"

__all__ = [
    "SiliconFlowClient",
    "SiliconFlowConfig",
    "SiliconFlowError",
    "RESOLUTIONS",
    "ASPECT_RATIOS",
    "VIDEO_SIZES",
    "SPEECH_MODELS",
    "DEFAULT_IMAGE_MODEL",
    "resolve_image_size",
    "download_file",
    "save_binary_file",
    "__version__",
]


class SiliconFlowClient(ImagesMixin, VideosMixin, AudioMixin, AccountMixin, _SiliconFlowBase):
    """硅基流动 API 异步客户端，聚合图像 / 视频 / 语音 / 账户能力。"""

    @classmethod
    def from_env(cls) -> SiliconFlowClient:
        """从环境变量构造客户端。"""
        return cls(SiliconFlowConfig.from_env())
