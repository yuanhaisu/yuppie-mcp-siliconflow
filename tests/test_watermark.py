"""关闭「AI 生成」水印的请求头与参数透传测试（打桩网络，不触网）"""

import asyncio

import httpx
import pytest
import yuppie_siliconflow.images as images_mod
from yuppie_mcp_siliconflow.tools import images as tool_images
from yuppie_siliconflow import SiliconFlowClient, SiliconFlowConfig
from yuppie_siliconflow.config import SiliconFlowConfig as _ConfigForType

_FAKE_PNG = b"\x89PNG\r\n\x1a\n payload"


@pytest.fixture
def stub_fetch(monkeypatch):
    """拦掉取字节请求：`_collect_image` 本来会真的去下载 S3 链接。"""

    async def _ok(_url, timeout=120.0):
        return _FAKE_PNG

    monkeypatch.setattr(images_mod, "fetch_bytes", _ok)


def _client(seen: list[httpx.Request], **config_kwargs) -> SiliconFlowClient:
    """构造一个把请求记进 `seen` 的客户端。"""
    client = SiliconFlowClient(SiliconFlowConfig(api_key="sk-test", **config_kwargs))

    async def _handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"images": [{"url": "https://s3.example/a.png"}], "seed": 7}
        )

    client._http = httpx.AsyncClient(  # noqa: SLF001 - 测试注入 MockTransport
        base_url="https://api.example",
        transport=httpx.MockTransport(_handler),
    )
    return client


def _watermark_header(request: httpx.Request) -> str | None:
    return request.headers.get("X-Enable-Watermark")


def test_generate_image_keeps_watermark_by_default(stub_fetch):
    """不传参数、配置也没开：不发这个头，行为与旧版一致。"""
    seen: list[httpx.Request] = []
    client = _client(seen)
    asyncio.run(client.generate_image("cat"))

    assert len(seen) == 1
    assert _watermark_header(seen[0]) is None


def test_generate_image_sends_header_when_disabled(stub_fetch):
    seen: list[httpx.Request] = []
    client = _client(seen)
    asyncio.run(client.generate_image("cat", disable_watermark=True))

    assert _watermark_header(seen[0]) == "0"


def test_config_default_applies_when_param_omitted(stub_fetch):
    seen: list[httpx.Request] = []
    client = _client(seen, disable_watermark=True)
    asyncio.run(client.generate_image("cat"))

    assert _watermark_header(seen[0]) == "0"


def test_explicit_param_overrides_config(stub_fetch):
    """配置开了关闭，但调用点显式传 False，应当重新带上水印（不发头）。"""
    seen: list[httpx.Request] = []
    client = _client(seen, disable_watermark=True)
    asyncio.run(client.generate_image("cat", disable_watermark=False))

    assert _watermark_header(seen[0]) is None


def test_edit_image_honours_disable_watermark(stub_fetch):
    seen: list[httpx.Request] = []
    client = _client(seen)
    asyncio.run(client.edit_image("https://s3.example/in.png", "换个背景", disable_watermark=True))

    assert _watermark_header(seen[0]) == "0"


@pytest.mark.parametrize(
    "raw,expected",
    [("1", True), ("true", True), ("TRUE", True), ("on", True), ("0", False), ("", False)],
)
def test_from_env_reads_disable_watermark(monkeypatch, raw, expected):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setenv("SILICONFLOW_DISABLE_WATERMARK", raw)
    assert _ConfigForType.from_env().disable_watermark is expected


def test_from_env_defaults_to_watermark_on(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.delenv("SILICONFLOW_DISABLE_WATERMARK", raising=False)
    assert SiliconFlowConfig.from_env().disable_watermark is False


def test_tool_forwards_disable_watermark_to_client(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeClient:
        async def generate_image(self, *_args, **kwargs):
            captured.update(kwargs)
            return {"model": "m", "size": None, "seed": None, "images": []}

    monkeypatch.setattr(tool_images, "get_client", lambda: _FakeClient())
    asyncio.run(
        tool_images.generate_image(
            tool_images.GenerateImageInput(prompt="cat", disable_watermark=True)
        )
    )
    assert captured["disable_watermark"] is True


def test_edit_tool_forwards_disable_watermark_to_client(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeClient:
        async def edit_image(self, *_args, **kwargs):
            captured.update(kwargs)
            return {"model": "m", "size": None, "seed": None, "images": []}

    monkeypatch.setattr(tool_images, "get_client", lambda: _FakeClient())
    asyncio.run(
        tool_images.edit_image(
            tool_images.EditImageInput(
                image="data:image/png;base64,AAA", prompt="x", disable_watermark=True
            )
        )
    )
    assert captured["disable_watermark"] is True
