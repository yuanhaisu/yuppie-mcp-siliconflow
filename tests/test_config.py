"""SiliconFlowConfig 环境变量读取与校验测试"""

import pytest
from yuppie_siliconflow.config import DEFAULT_BASE_URL, DEFAULT_IMAGE_MODEL, SiliconFlowConfig


def test_from_env_requires_api_key(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "")
    with pytest.raises(ValueError, match="SILICONFLOW_API_KEY"):
        SiliconFlowConfig.from_env()


def test_from_env_defaults(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "  sk-test  ")
    monkeypatch.delenv("SILICONFLOW_BASE_URL", raising=False)
    monkeypatch.delenv("SILICONFLOW_MODEL", raising=False)
    monkeypatch.delenv("SILICONFLOW_IMAGE_DIR", raising=False)

    cfg = SiliconFlowConfig.from_env()
    assert cfg.api_key == "sk-test"
    assert cfg.base_url == DEFAULT_BASE_URL
    assert cfg.default_image_model == DEFAULT_IMAGE_MODEL
    assert cfg.image_dir is None


def test_from_env_overrides_and_trailing_slash(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/")
    monkeypatch.setenv("SILICONFLOW_MODEL", "black-forest-labs/FLUX.1-Kontext-pro")
    monkeypatch.setenv("SILICONFLOW_IMAGE_DIR", "/tmp/imgs")

    cfg = SiliconFlowConfig.from_env()
    assert cfg.base_url == "https://api.siliconflow.cn"
    assert cfg.default_image_model == "black-forest-labs/FLUX.1-Kontext-pro"
    assert cfg.image_dir == "/tmp/imgs"
