"""MCP 工具入参 Pydantic 校验测试"""

import asyncio

import pytest
from pydantic import ValidationError
from yuppie_mcp_siliconflow.tools import images


def test_generate_image_requires_prompt():
    with pytest.raises(ValidationError):
        images.GenerateImageInput(prompt="")


def test_generate_image_defaults_match_reference():
    """默认值与 stevefordev/siliconflow-mcp 对齐。"""
    inp = images.GenerateImageInput(prompt="cat")
    assert inp.aspect_ratio == "1:1"
    assert inp.image_size is None
    assert inp.num_images == 1
    assert inp.output_format == "png"
    assert inp.model is None
    assert inp.seed is None
    assert inp.negative_prompt is None


def test_generate_image_num_images_bounds():
    with pytest.raises(ValidationError):
        images.GenerateImageInput(prompt="cat", num_images=9)
    ok = images.GenerateImageInput(prompt="cat", num_images=4)
    assert ok.num_images == 4


def test_edit_image_requires_image_and_prompt():
    with pytest.raises(ValidationError):
        images.EditImageInput(image="", prompt="x")
    with pytest.raises(ValidationError):
        images.EditImageInput(image="data:image/png;base64,AAA", prompt="")
    ok = images.EditImageInput(image="data:image/png;base64,AAA", prompt="换个背景")
    assert ok.model is None


def test_tools_package_exposes_only_images():
    """收敛为纯图像工具集后，tools 包只应有 images 一个模块。"""
    from yuppie_mcp_siliconflow import tools

    assert tools.__all__ == ["images"]


def test_format_summary_has_no_img_tag():
    """回归护栏：图片改用原生内容块后，摘要里不能再出现 <img>。"""
    result = {
        "model": "Tongyi-MAI/Z-Image-Turbo",
        "size": "1024x576",
        "seed": 433257550,
        "images": [
            {
                "url": "https://s3.example/x.png?sig=1",
                "local_path": None,
                "content": b"\x89PNG\r\n\x1a\n",
                "format": "png",
            }
        ],
    }
    summary = images._format_summary(result, "生成")
    assert "<img" not in summary
    assert "1024x576" in summary
    assert "433257550" in summary
    assert "https://s3.example/x.png?sig=1" in summary


def test_to_tool_result_skips_images_without_bytes():
    """取字节失败的那张不进 images（只保留在文本摘要里），避免回吐空图片块。"""
    result = {
        "model": "m",
        "size": "512x512",
        "seed": None,
        "images": [
            {
                "url": "https://s3.example/a.png",
                "local_path": "/tmp/a.png",
                "content": b"\x89PNG\r\n\x1a\n",
                "format": "png",
            },
            {
                "url": "https://s3.example/b.png",
                "local_path": None,
                "content": None,
                "format": "png",
            },
        ],
    }
    out = images._to_tool_result(result, "生成")
    assert len(out.images) == 1
    assert out.images[0].data.startswith(b"\x89PNG")
    assert out.images[0].format == "png"
    assert out.images[0].local_path == "/tmp/a.png"
    assert "未取到字节" in out.summary


def test_generate_image_packs_bytes(monkeypatch):
    """打桩网络：库层返回的字节被工具层打包进 ImageData。"""

    class _FakeClient:
        async def generate_image(self, *_args, **_kwargs):
            return {
                "model": "m",
                "size": "512x512",
                "seed": 7,
                "images": [
                    {
                        "url": "https://s3.example/a.png",
                        "local_path": None,
                        "content": b"\x89PNG\r\n\x1a\n",
                        "format": "png",
                    }
                ],
            }

    monkeypatch.setattr(images, "get_client", lambda: _FakeClient())
    out = asyncio.run(images.generate_image(images.GenerateImageInput(prompt="cat")))
    assert len(out.images) == 1
    assert out.images[0].data[:4] == b"\x89PNG"
    assert "<img" not in out.summary


def test_generate_image_error_is_text_only(monkeypatch):
    def _boom():
        raise RuntimeError("no api key")

    monkeypatch.setattr(images, "get_client", _boom)
    out = asyncio.run(images.generate_image(images.GenerateImageInput(prompt="cat")))
    assert out.images == []
    assert out.summary.startswith("❌ 生成图像失败")
