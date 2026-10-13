"""SiliconFlowClient 底层测试（纯函数，不触网）"""

import httpx
import pytest
from yuppie_siliconflow import ASPECT_RATIOS, SiliconFlowClient, SiliconFlowConfig
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
