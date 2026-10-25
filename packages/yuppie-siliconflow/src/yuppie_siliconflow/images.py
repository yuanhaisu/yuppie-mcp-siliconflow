"""文生图 / 图生图（SiliconFlow /v1/images/generations）"""

from __future__ import annotations

from typing import Any

from .files import fetch_bytes, guess_image_format, save_binary_file

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


async def _collect_image(
    url: str | None,
    *,
    save_dir: str | None,
    prefix: str,
) -> dict[str, Any]:
    """取回单张图的字节，供上层内联为 MCP image 内容块。

    取字节**总是**执行（内联展示的前提）；``save_dir`` 非空时才额外落盘。
    任一环节失败都只降级、不中断主流程，保证至少能回吐 URL。
    """
    item: dict[str, Any] = {
        "url": url,
        "local_path": None,
        "content": None,
        "format": guess_image_format(url) if url else "png",
    }
    if not url:
        return item

    try:
        content = await fetch_bytes(url)
    except Exception as exc:  # noqa: BLE001 - 取字节失败不应中断主流程
        print(f"[yuppie-siliconflow] 取图失败，仅返回 URL：{exc}")
        return item

    item["content"] = content

    if save_dir:
        try:
            item["local_path"] = save_binary_file(content, save_dir, item["format"], prefix)
        except Exception as exc:  # noqa: BLE001 - 落盘失败不应中断主流程
            print(f"[yuppie-siliconflow] 落盘失败：{exc}")

    return item


class ImagesMixin:
    """图片生成能力。"""

    # 由 _SiliconFlowBase 提供
    _config: Any
    _request: Any
    _raise_for_status: Any

    def _watermark_headers(self, disable: bool | None) -> dict[str, str] | None:
        """把「关闭水印」翻译成 SiliconFlow 的请求头。

        ``disable`` 为 None 时回落到配置（``SILICONFLOW_DISABLE_WATERMARK``）。
        返回 None 表示不附加任何头 —— 与旧版本行为完全一致（保留水印）。
        """
        enabled = self._config.disable_watermark if disable is None else disable
        if not enabled:
            return None
        return {"X-Enable-Watermark": "0"}

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
        disable_watermark: bool | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """生成图像，返回 ``{"model", "size", "seed", "images": [...]}``。

        每个 image 项为 ``{"url", "local_path", "content", "format"}``：
        ``content`` 是图片字节（供上层内联为 MCP image 内容块），
        ``local_path`` 仅在配置了 ``SILICONFLOW_IMAGE_DIR`` 时才有值。

        ``disable_watermark`` 为 None 时跟随 ``SILICONFLOW_DISABLE_WATERMARK``；
        关闭后不再在右下角叠加「AI 生成」水印。
        """
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

        resp = await self._request(
            "POST",
            "/v1/images/generations",
            json=payload,
            headers=self._watermark_headers(disable_watermark),
        )
        self._raise_for_status(resp, "生成图像")

        data = resp.json()
        images = data.get("images") or []
        if not images:
            raise RuntimeError("SiliconFlow 未返回任何图像")

        save_dir = self._config.image_dir if save else None
        results = [
            await _collect_image(img.get("url"), save_dir=save_dir, prefix="img")
            for img in images
        ]

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
        disable_watermark: bool | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """基于已有图像（URL 或 base64）按提示词编辑，返回同 generate_image 的结构。"""
        use_model = model or DEFAULT_EDIT_MODEL
        payload = {"model": use_model, "prompt": prompt, "image": image}

        resp = await self._request(
            "POST",
            "/v1/images/generations",
            json=payload,
            headers=self._watermark_headers(disable_watermark),
        )
        self._raise_for_status(resp, "编辑图像")

        data = resp.json()
        images = data.get("images") or []
        if not images:
            raise RuntimeError("SiliconFlow 未返回任何图像")

        save_dir = self._config.image_dir if save else None
        collected = await _collect_image(images[0].get("url"), save_dir=save_dir, prefix="edit")

        return {
            "model": use_model,
            "size": None,
            "seed": data.get("seed"),
            "images": [collected],
        }
