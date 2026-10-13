"""SiliconFlow 配置：从环境变量读取 API Key、Base URL、默认模型与保存目录"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://api.siliconflow.com"
DEFAULT_IMAGE_MODEL = "Tongyi-MAI/Z-Image-Turbo"


def load_dotenv(path: str = ".env") -> None:
    """轻量 .env 加载器（无第三方依赖）。

    仅在环境变量尚未设置时写入，不覆盖已有值。文件不存在时静默跳过。
    """
    env_path = Path(path)
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class SiliconFlowConfig:
    """SiliconFlow 客户端配置。"""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    default_image_model: str = DEFAULT_IMAGE_MODEL
    image_dir: str | None = None

    @classmethod
    def from_env(cls) -> SiliconFlowConfig:
        """从环境变量（含当前目录 .env）构造配置。"""
        load_dotenv()
        api_key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("未设置 SILICONFLOW_API_KEY 环境变量")

        base_url = (os.getenv("SILICONFLOW_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
        model = (os.getenv("SILICONFLOW_MODEL") or DEFAULT_IMAGE_MODEL).strip()
        image_dir = (os.getenv("SILICONFLOW_IMAGE_DIR") or "").strip() or None

        return cls(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            default_image_model=model or DEFAULT_IMAGE_MODEL,
            image_dir=image_dir,
        )
