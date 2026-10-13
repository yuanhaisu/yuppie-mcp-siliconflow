"""文生图 / 图生图（SiliconFlow /v1/images/generations）"""

from __future__ import annotations

from typing import Any

from .files import download_file

DEFAULT_EDIT_MODEL = "Qwen/Qwen-Image-Edit"
DEFAULT_IMAGE_SIZE = "1024x1024"

# 通用比例 → 尺寸。未指定模型、或模型不在下表时使用。
ASPECT_RATIOS: dict[str, str] = {
    "1:1": "1024x1024",
    "3:4": "768x1024",
    "4:3": "1024x768",
    "9:16": "576x1024",
    "16:9": "1024x576",
}

# 显式分辨率枚举（沿用旧 TS 版的取值）
RESOLUTIONS = ["1024x1024", "960x1280", "768x1024", "720x1440", "720x1280"]

# 各模型的比例 → 尺寸映射，取自官方文档给出的推荐值。
#
# 模型之间的尺寸档位差异很大（512 档 / 1328 档 / 1024 档），用一张全局表会把模型
# 不认识的尺寸发出去 —— 例如默认模型 Z-Image 的推荐集里就没有 1024x1024。
MODEL_ASPECT_SIZES: dict[str, dict[str, str]] = {
    "Tongyi-MAI/Z-Image-Turbo": {
        "1:1": "512x512",
        "3:4": "768x1024",
        "16:9": "1024x576",
        "9:16": "576x1024",
    },
    "black-forest-labs/FLUX.2-pro": {
        "1:1": "512x512",
        "3:4": "768x1024",
        "4:3": "1024x768",
        "9:16": "576x1024",
        "16:9": "1024x576",
    },
    "black-forest-labs/FLUX.2-flex": {
        "1:1": "512x512",
        "3:4": "768x1024",
        "4:3": "1024x768",
        "9:16": "576x1024",
        "16:9": "1024x576",
    },
    "Qwen/Qwen-Image": {
        "1:1": "1328x1328",
        "16:9": "1664x928",
        "9:16": "928x1664",
        "4:3": "1472x1140",
        "3:4": "1140x1472",
        "3:2": "1584x1056",
        "2:3": "1056x1584",
    },
    "Qwen/Qwen-Image-Edit": {
        "1:1": "1328x1328",
        "16:9": "1664x928",
        "9:16": "928x1664",
        "4:3": "1472x1140",
        "3:4": "1140x1472",
        "3:2": "1584x1056",
        "2:3": "1056x1584",
    },
    "black-forest-labs/FLUX-1.1-pro": {
        "1:1": "1024x1024",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "16:9": "1280x720",
        "9:16": "720x1280",
    },
    "black-forest-labs/FLUX-1.1-pro-Ultra": {
        "1:1": "1024x1024",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "16:9": "1280x720",
        "9:16": "720x1280",
    },
    "black-forest-labs/FLUX.1-schnell": {
        "1:1": "1024x1024",
        "3:4": "768x1024",
        "16:9": "1024x576",
        "9:16": "576x1024",
    },
    "black-forest-labs/FLUX.1-dev": {
        "1:1": "1024x1024",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "16:9": "1280x720",
        "9:16": "720x1280",
    },
}


def resolve_image_size(
    image_size: str | None,
    aspect_ratio: str | None,
    model: str | None = None,
) -> str:
    """解析最终尺寸：显式尺寸 > 按模型查比例映射 > 该模型的方形尺寸。"""
    if image_size:
        return image_size
    table = MODEL_ASPECT_SIZES.get(model or "", ASPECT_RATIOS)
    if aspect_ratio and aspect_ratio in table:
        return table[aspect_ratio]
    return table.get("1:1", DEFAULT_IMAGE_SIZE)


class ImagesMixin:
    """图片生成能力。"""

    # 由 _SiliconFlowBase 提供
    _config: Any
    _request: Any
    _raise_for_status: Any

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        aspect_ratio: str | None = "1:1",
        image_size: str | None = None,
        num_images: int = 1,
        seed: int | None = None,
        negative_prompt: str | None = None,
        output_format: str = "png",
        save: bool = True,
    ) -> dict[str, Any]:
        """生成图像，返回 ``{"model", "size", "seed", "images": [{"url", "local_path"}]}``。"""
        use_model = model or self._config.default_image_model
        size = resolve_image_size(image_size, aspect_ratio, use_model)

        payload: dict[str, Any] = {
            "model": use_model,
            "prompt": prompt,
            "image_size": size,
            "output_format": output_format,
            "batch_size": min(max(num_images, 1), 4),
        }
        if seed is not None:
            payload["seed"] = seed
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        resp = await self._request("POST", "/v1/images/generations", json=payload)
        self._raise_for_status(resp, "生成图像")

        data = resp.json()
        images = data.get("images") or []
        if not images:
            raise RuntimeError("SiliconFlow 未返回任何图像")

        results: list[dict[str, Any]] = []
        for img in images:
            url = img.get("url")
            local_path: str | None = None
            if save and url and self._config.image_dir:
                local_path = await download_file(url, self._config.image_dir, "img")
            results.append({"url": url, "local_path": local_path})

        return {
            "model": use_model,
            "size": size,
            "seed": data.get("seed", seed),
            "images": results,
        }

    async def edit_image(
        self,
        image: str,
        prompt: str,
        *,
        model: str | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """基于已有图像（URL 或 base64）按提示词编辑，返回同 generate_image 的结构。"""
        use_model = model or DEFAULT_EDIT_MODEL
        payload = {"model": use_model, "prompt": prompt, "image": image}

        resp = await self._request("POST", "/v1/images/generations", json=payload)
        self._raise_for_status(resp, "编辑图像")

        data = resp.json()
        images = data.get("images") or []
        if not images:
            raise RuntimeError("SiliconFlow 未返回任何图像")

        url = images[0].get("url")
        local_path: str | None = None
        if save and url and self._config.image_dir:
            local_path = await download_file(url, self._config.image_dir, "edit")

        return {
            "model": use_model,
            "size": None,
            "seed": data.get("seed"),
            "images": [{"url": url, "local_path": local_path}],
        }
