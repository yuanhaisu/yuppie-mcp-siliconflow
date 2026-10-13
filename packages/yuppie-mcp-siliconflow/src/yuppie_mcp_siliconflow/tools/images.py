"""图片生成工具：generate_image / edit_image"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from yuppie_siliconflow import ASPECT_RATIOS, RESOLUTIONS

from ._client import get_client


class GenerateImageInput(BaseModel):
    """generate_image 入参。"""

    prompt: str = Field(..., min_length=1, description="图像提示词，建议英文效果更好")
    resolution: str | None = Field(
        None,
        description=f"显式分辨率，可选：{' / '.join(RESOLUTIONS)}；不填则用 aspect_ratio",
    )
    aspect_ratio: str | None = Field(
        None, description=f"宽高比，可选：{' / '.join(ASPECT_RATIOS)}"
    )
    model: str | None = Field(
        None, description="模型 ID；不填用 SILICONFLOW_MODEL 或默认 Tongyi-MAI/Z-Image-Turbo"
    )
    seed: int | None = Field(None, ge=0, description="随机种子，用于复现同一张图")
    negative_prompt: str | None = Field(None, description="负面提示词（仅部分模型支持）")
    batch_size: int = Field(1, ge=1, le=4, description="生成张数（1-4）")
    output_format: str = Field("png", description="输出格式：png / jpeg")


class EditImageInput(BaseModel):
    """edit_image 入参。"""

    image: str = Field(..., min_length=1, description="待编辑图像的 URL 或 base64")
    prompt: str = Field(..., min_length=1, description="编辑指令，如“把背景换成海边”")
    model: str | None = Field(None, description="编辑模型，默认 Qwen/Qwen-Image-Edit-2509")


def _alt_text(prompt: str) -> str:
    cleaned = prompt[:50].replace('"', " ").replace("<", " ").replace(">", " ")
    return cleaned + ("..." if len(prompt) > 50 else "")


def _format_images(result: dict[str, Any], prompt: str) -> str:
    alt = _alt_text(prompt)
    lines: list[str] = []
    for idx, item in enumerate(result.get("images", []), start=1):
        url = item.get("url")
        local_path = item.get("local_path")
        if local_path:
            lines.append(f"{idx}. 本地文件：`{local_path}`")
        if url:
            lines.append(f'{idx}. 在线图片：<img src="{url}" alt="{alt}">')
    if not lines:
        return "❌ 生成图像失败：未返回任何图像"

    size = result.get("size")
    seed = result.get("seed")
    header = f"✅ 已生成 {size} 图像（模型：{result.get('model')}）" if size else (
        f"✅ 图像生成完成（模型：{result.get('model')}）"
    )
    if seed is not None:
        header += f"，Seed：{seed}"
    lines.append("")
    lines.append("请为上面的 `<img>` 添加 `width` 属性（200~500 像素）后原样发送给用户。")
    return "\n".join([header, *lines])


async def generate_image(inp: GenerateImageInput) -> str:
    """根据提示词生成图像。默认模型 Z-Image-Turbo 规避 S3 签名坑。"""
    try:
        client = get_client()
        result = await client.generate_image(
            inp.prompt,
            resolution=inp.resolution,
            aspect_ratio=inp.aspect_ratio,
            model=inp.model,
            seed=inp.seed,
            negative_prompt=inp.negative_prompt,
            batch_size=inp.batch_size,
            output_format=inp.output_format,
        )
        return _format_images(result, inp.prompt)
    except Exception as exc:  # noqa: BLE001 - 统一转为可读错误
        return f"❌ 生成图像失败：{exc}"


async def edit_image(inp: EditImageInput) -> str:
    """基于已有图像按指令编辑。"""
    try:
        client = get_client()
        result = await client.edit_image(inp.image, inp.prompt, model=inp.model)
        return _format_images(result, inp.prompt)
    except Exception as exc:  # noqa: BLE001
        return f"❌ 编辑图像失败：{exc}"
