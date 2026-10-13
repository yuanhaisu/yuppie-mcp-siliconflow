"""MCP 工具入参 Pydantic 校验测试"""

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
