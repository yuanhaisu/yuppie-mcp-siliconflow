"""图片生成工具：generate_image / edit_image

本模块**不 import mcp**：只产出中性结果对象（文本摘要 + 图片字节），
由 ``server.py`` 负责转成 MCP 的 ``TextContent`` / ``ImageContent`` 内容块。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field
from yuppie_siliconflow import ASPECT_RATIOS, RESOLUTIONS

from ._client import get_client

_ASPECT_LIST = " / ".join(ASPECT_RATIOS)
_RESOLUTION_LIST = " / ".join(RESOLUTIONS)


class GenerateImageInput(BaseModel):
    """generate_image 入参。"""

    prompt: str = Field(..., min_length=1, description="图像提示词，建议英文效果更好")
    model: str | None = Field(
        None, description="模型 ID；不填用 SILICONFLOW_MODEL 或默认 Tongyi-MAI/Z-Image-Turbo"
    )
    aspect_ratio: str = Field("1:1", description=f"宽高比，可选：{_ASPECT_LIST}")
    image_size: str | None = Field(
        None, description=f"显式尺寸 WxH，如 {_RESOLUTION_LIST}；填了就忽略 aspect_ratio"
    )
    num_images: int = Field(1, ge=1, le=4, description="生成张数（1-4）")
    seed: int | None = Field(None, ge=0, description="随机种子，用于复现同一张图")
    negative_prompt: str | None = Field(None, description="负面提示词（仅部分模型支持）")
    output_format: str = Field("png", description="输出格式：png / jpeg")
    disable_watermark: bool | None = Field(
        None,
        description=(
            "关闭右下角的「AI 生成」水印；不填则跟随 SILICONFLOW_DISABLE_WATERMARK，"
            "两者都未指定时保留水印"
        ),
    )


class EditImageInput(BaseModel):
    """edit_image 入参。"""

    image: str = Field(..., min_length=1, description="待编辑图像的 URL 或 base64")
    prompt: str = Field(..., min_length=1, description="编辑指令，如“把背景换成海边”")
    model: str | None = Field(None, description="编辑模型，默认 Qwen/Qwen-Image-Edit")
    disable_watermark: bool | None = Field(
        None,
        description=(
            "关闭右下角的「AI 生成」水印；不填则跟随 SILICONFLOW_DISABLE_WATERMARK，"
            "两者都未指定时保留水印"
        ),
    )


@dataclass
class ImageData:
    """单张图片的字节与格式，由 server 层包装成 MCP ``Image``。"""

    data: bytes
    format: str = "png"
    url: str | None = None
    local_path: str | None = None


@dataclass
class ImageToolResult:
    """工具结果：文本摘要 + 待内联的图片块列表。"""

    summary: str
    images: list[ImageData] = field(default_factory=list)


def _format_summary(result: dict[str, Any], action: str) -> str:
    """拼文本摘要（模型名 / 尺寸 / Seed / 在线链接 / 本地路径）。

    图片本体已由 ``ImageContent`` 块承载，这里**不再**输出 ``<img>`` 标签。
    """
    lines: list[str] = []
    for idx, item in enumerate(result.get("images", []), start=1):
        if item.get("local_path"):
            lines.append(f"{idx}. 本地文件：`{item['local_path']}`")
        if item.get("url"):
            lines.append(f"{idx}. 在线链接（24 小时内有效）：{item['url']}")
        if not item.get("content"):
            lines.append(f"{idx}. 该张图片未取到字节，仅能提供上面的链接")

    size = result.get("size")
    header = (
        f"✅ 已{action} {size} 图像（模型：{result.get('model')}）"
        if size
        else f"✅ 图像{action}完成（模型：{result.get('model')}）"
    )
    seed = result.get("seed")
    if seed is not None:
        header += f"，Seed：{seed}"

    return "\n".join([header, *lines]) if lines else header


def _to_tool_result(result: dict[str, Any], action: str) -> ImageToolResult:
    """把库包的返回结构转成工具结果对象。"""
    return ImageToolResult(
        summary=_format_summary(result, action),
        images=[
            ImageData(
                data=item["content"],
                format=item.get("format") or "png",
                url=item.get("url"),
                local_path=item.get("local_path"),
            )
            for item in result.get("images", [])
            if item.get("content")
        ],
    )


async def generate_image(inp: GenerateImageInput) -> ImageToolResult:
    """根据提示词生成图像。默认模型 Z-Image-Turbo 规避 S3 签名坑。"""
    try:
        client = get_client()
        result = await client.generate_image(
            inp.prompt,
            model=inp.model,
            aspect_ratio=inp.aspect_ratio,
            image_size=inp.image_size,
            num_images=inp.num_images,
            seed=inp.seed,
            negative_prompt=inp.negative_prompt,
            output_format=inp.output_format,
            disable_watermark=inp.disable_watermark,
        )
        return _to_tool_result(result, "生成")
    except Exception as exc:  # noqa: BLE001 - 统一转为可读错误
        return ImageToolResult(summary=f"❌ 生成图像失败：{exc}")


async def edit_image(inp: EditImageInput) -> ImageToolResult:
    """基于已有图像按指令编辑。"""
    try:
        client = get_client()
        result = await client.edit_image(
            inp.image,
            inp.prompt,
            model=inp.model,
            disable_watermark=inp.disable_watermark,
        )
        return _to_tool_result(result, "编辑")
    except Exception as exc:  # noqa: BLE001
        return ImageToolResult(summary=f"❌ 编辑图像失败：{exc}")
