"""server 层：工具结果 → MCP 内容块"""

import asyncio
import base64

from mcp.types import TextContent
from yuppie_mcp_siliconflow.server import _to_content, mcp
from yuppie_mcp_siliconflow.tools.images import ImageData, ImageToolResult

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_to_content_returns_text_then_image_block():
    out = ImageToolResult(
        summary="✅ 已生成 512x512 图像（模型：m）",
        images=[ImageData(data=_PNG_MAGIC + b"rest", format="png", url="https://x/a.png")],
    )
    content = _to_content(out)
    assert len(content) == 2
    assert isinstance(content[0], TextContent)
    assert content[0].text.startswith("✅")

    image_content = content[1].to_image_content()
    assert image_content.type == "image"
    # 必须是 image/png：S3 常回 application/octet-stream，客户端靠 mimeType 决定渲不渲染
    assert image_content.mime_type == "image/png"
    assert base64.b64decode(image_content.data).startswith(_PNG_MAGIC)


def test_to_content_maps_jpeg_format():
    out = ImageToolResult(
        summary="x", images=[ImageData(data=b"\xff\xd8\xff\xe0", format="jpeg")]
    )
    assert _to_content(out)[1].to_image_content().mime_type == "image/jpeg"


def test_to_content_error_result_is_text_only():
    content = _to_content(ImageToolResult(summary="❌ 生成图像失败：boom"))
    assert len(content) == 1
    assert isinstance(content[0], TextContent)


def test_image_tools_advertise_no_output_schema():
    """返回内容块的工具不应生成 outputSchema，否则客户端会去解析结构化输出。"""
    tools = asyncio.run(mcp.list_tools())
    by_name = {tool.name: tool for tool in tools}
    assert set(by_name) == {"generate_image", "edit_image"}
    for tool in by_name.values():
        assert tool.output_schema is None
