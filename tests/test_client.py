"""SiliconFlowClient 底层测试（纯函数，不触网）"""

import asyncio
from pathlib import Path

import httpx
import pytest
from yuppie_siliconflow import (
    ASPECT_RATIOS,
    SiliconFlowClient,
    SiliconFlowConfig,
    guess_image_format,
)
from yuppie_siliconflow.base import _SiliconFlowBase
from yuppie_siliconflow.images import resolve_image_size


@pytest.mark.parametrize(
    "resolution,aspect,expected",
    [
        ("960x1280", "1:1", "960x1280"),  # 显式分辨率优先
        (None, "16:9", "1024x576"),
        (None, "1:1", "1024x1024"),
        (None, None, "1024x1024"),
        (None, "999", "1024x1024"),  # 未知宽高比回落默认
    ],
)
def test_resolve_image_size(resolution, aspect, expected):
    assert resolve_image_size(resolution, aspect) == expected


def test_aspect_ratios_mapping():
    assert ASPECT_RATIOS["3:4"] == "768x1024"


def test_format_error_json():
    resp = httpx.Response(400, json={"message": "bad prompt"})
    assert "400" in _SiliconFlowBase._format_error(resp)
    assert "bad prompt" in _SiliconFlowBase._format_error(resp)


def test_format_error_non_json():
    resp = httpx.Response(500, text="boom")
    assert _SiliconFlowBase._format_error(resp) == "HTTP 500 - boom"


def test_client_exposes_all_capabilities():
    client = SiliconFlowClient(SiliconFlowConfig(api_key="sk-test"))
    for method in (
        "generate_image",
        "edit_image",
    ):
        assert callable(getattr(client, method))

    # 账户能力已移除
    assert not hasattr(client, "list_models")


def test_guess_image_format():
    assert guess_image_format("https://s3.example/y_00001_.png?X-Amz-Signature=1") == "png"
    assert guess_image_format("https://s3.example/y.jpg") == "jpeg"
    assert guess_image_format("https://s3.example/y.jpeg?x=1") == "jpeg"
    assert guess_image_format("https://s3.example/y") == "png"  # 未知扩展名回落 png


def test_collect_image_degrades_on_download_failure(monkeypatch):
    """取字节失败只降级（content=None + 保留 URL），不抛异常。"""
    import yuppie_siliconflow.images as images_mod

    async def _boom(_url, timeout=120.0):
        raise RuntimeError("403 SignatureDoesNotMatch")

    monkeypatch.setattr(images_mod, "fetch_bytes", _boom)
    item = asyncio.run(
        images_mod._collect_image("https://s3.example/a.png", save_dir=None, prefix="img")
    )
    assert item["content"] is None
    assert item["url"] == "https://s3.example/a.png"
    assert item["format"] == "png"


def test_collect_image_inlines_and_optionally_saves(monkeypatch, tmp_path):
    import yuppie_siliconflow.images as images_mod

    async def _ok(_url, timeout=120.0):
        return b"\x89PNG\r\n\x1a\n payload"

    monkeypatch.setattr(images_mod, "fetch_bytes", _ok)

    # 不配目录：只取字节内联，不落盘
    inline_only = asyncio.run(
        images_mod._collect_image("https://s3.example/a.png", save_dir=None, prefix="img")
    )
    assert inline_only["content"].startswith(b"\x89PNG")
    assert inline_only["local_path"] is None

    # 配了目录：额外落盘
    saved = asyncio.run(
        images_mod._collect_image(
            "https://s3.example/a.png", save_dir=str(tmp_path), prefix="img"
        )
    )
    assert saved["local_path"] is not None
    assert Path(saved["local_path"]).read_bytes().startswith(b"\x89PNG")
