"""文生图 / 图生图（SiliconFlow /v1/images/generations）"""

from __future__ import annotations

from typing import Any

from .files import download_file

# 显式分辨率（沿用旧 TS 版的枚举）
RESOLUTIONS = ["1024x1024", "960x1280", "768x1024", "720x1440", "720x1280"]

# 宽高比 → 显式尺寸（沿用 stevefordev/siliconflow-mcp 的映射）
ASPECT_RATIOS: dict[str, str] = {
    "1:1": "1024x1024",
    "3:4": "768x1024",
    "4:3": "1024x768",
    "9:16": "576x1024",
    "16:9": "1024x576",
}

DEFAULT_EDIT_MODEL = "Qwen/Qwen-Image-Edit"


def resolve_image_size(resolution: str | None, aspect_ratio: str | None) -> str:
    """分辨率优先；其次宽高比映射；都没有则 1024x1024。"""
    if resolution:
        return resolution
    if aspect_ratio and aspect_ratio in ASPECT_RATIOS:
        return ASPECT_RATIOS[aspect_ratio]
    return "1024x1024"


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
        resolution: str | None = None,
        aspect_ratio: str | None = None,
        model: str | None = None,
        seed: int | None = None,
        negative_prompt: str | None = None,
        batch_size: int = 1,
        output_format: str = "png",
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """生成图像，返回 ``{"model", "size", "seed", "images": [{"url", "local_path"}]}``。"""
        size = resolve_image_size(resolution, aspect_ratio)
        use_model = model or self._config.default_image_model

        payload: dict[str, Any] = {
            "model": use_model,
            "prompt": prompt,
            "image_size": size,
            "output_format": output_format,
            "batch_size": min(max(batch_size, 1), 4),
        }
        if seed is not None:
            payload["seed"] = seed
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if num_inference_steps is not None:
            payload["num_inference_steps"] = num_inference_steps
        if guidance_scale is not None:
            payload["guidance_scale"] = guidance_scale

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
