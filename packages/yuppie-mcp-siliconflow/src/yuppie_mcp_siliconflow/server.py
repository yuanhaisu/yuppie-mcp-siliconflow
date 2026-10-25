"""SiliconFlow MCP Server 主入口"""

from __future__ import annotations

import os
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.utilities.types import Image
from mcp.types import TextContent, ToolAnnotations
from pydantic import Field

from . import __version__
from .tools import images

mcp = MCPServer(
    name="siliconflow_mcp",
    instructions=(
        "硅基流动（SiliconFlow）图像工具集：文生图与图生图/编辑。"
        "默认文生图模型为 Tongyi-MAI/Z-Image-Turbo。"
    ),
    version=__version__,
)


def _to_content(result: images.ImageToolResult) -> list[TextContent | Image]:
    """把工具结果转成 MCP 内容块：文本摘要 + 原生图片块。

    图片以 ``ImageContent`` 返回，由客户端原生组件渲染 —— 不经过 markdown/HTML
    sanitizer，也不依赖 24 小时过期的临时签名 URL。
    """
    content: list[TextContent | Image] = [TextContent(type="text", text=result.summary)]
    content.extend(Image(data=item.data, format=item.format) for item in result.images)
    return content


# ═══════════════════════════════════════════
# 图像工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="generate_image",
    annotations=ToolAnnotations(
        title="文生图",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_generate_image(
    prompt: Annotated[str, Field(description="图像提示词，建议英文效果更好", min_length=1)],
    model: Annotated[
        str | None,
        Field(description="模型 ID；不填用 SILICONFLOW_MODEL 或默认 Tongyi-MAI/Z-Image-Turbo"),
    ] = None,
    aspect_ratio: Annotated[
        str, Field(description="宽高比：1:1 / 3:4 / 4:3 / 9:16 / 16:9")
    ] = "1:1",
    image_size: Annotated[
        str | None,
        Field(
            description=(
                "显式尺寸 WxH，如 1024x1024 / 960x1280 / 768x1024；"
                "填了就忽略 aspect_ratio"
            )
        ),
    ] = None,
    num_images: Annotated[int, Field(description="生成张数（1-4）", ge=1, le=4)] = 1,
    seed: Annotated[int | None, Field(description="随机种子，用于复现", ge=0)] = None,
    negative_prompt: Annotated[
        str | None, Field(description="负面提示词（仅部分模型支持）")
    ] = None,
    output_format: Annotated[str, Field(description="输出格式：png / jpeg")] = "png",
    disable_watermark: Annotated[
        bool | None,
        Field(
            description=(
                "关闭右下角的「AI 生成」水印；不填则跟随 SILICONFLOW_DISABLE_WATERMARK，"
                "两者都未指定时保留水印"
            )
        ),
    ] = None,
) -> list[TextContent | Image]:
    """根据提示词生成图像。

    图像已作为**图片块**返回，客户端会直接渲染 —— 无需再输出 `<img>` 标签、
    也不要把 URL 当作图片发给用户。返回的文本里附带 24 小时有效的在线链接，
    仅供人工需要时取用。"""
    return _to_content(
        await images.generate_image(
            images.GenerateImageInput(
                prompt=prompt,
                model=model,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                num_images=num_images,
                seed=seed,
                negative_prompt=negative_prompt,
                output_format=output_format,
                disable_watermark=disable_watermark,
            )
        )
    )


# ✅
@mcp.tool(
    name="edit_image",
    annotations=ToolAnnotations(
        title="图生图 / 图像编辑",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_edit_image(
    image: Annotated[str, Field(description="待编辑图像的 URL 或 base64", min_length=1)],
    prompt: Annotated[str, Field(description="编辑指令", min_length=1)],
    model: Annotated[
        str | None, Field(description="编辑模型，默认 Qwen/Qwen-Image-Edit")
    ] = None,
    disable_watermark: Annotated[
        bool | None,
        Field(
            description=(
                "关闭右下角的「AI 生成」水印；不填则跟随 SILICONFLOW_DISABLE_WATERMARK，"
                "两者都未指定时保留水印"
            )
        ),
    ] = None,
) -> list[TextContent | Image]:
    """基于已有图像按指令编辑。图像以**图片块**返回，直接展示即可。"""
    return _to_content(
        await images.edit_image(
            images.EditImageInput(
                image=image,
                prompt=prompt,
                model=model,
                disable_watermark=disable_watermark,
            )
        )
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
