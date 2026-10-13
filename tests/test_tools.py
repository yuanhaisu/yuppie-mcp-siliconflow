"""MCP 工具入参 Pydantic 校验测试"""

import pytest
from pydantic import ValidationError
from yuppie_mcp_siliconflow.tools import account, audio, images, videos


def test_generate_image_requires_prompt():
    with pytest.raises(ValidationError):
        images.GenerateImageInput(prompt="")


def test_generate_image_batch_bounds():
    with pytest.raises(ValidationError):
        images.GenerateImageInput(prompt="cat", batch_size=9)
    ok = images.GenerateImageInput(prompt="cat", batch_size=4)
    assert ok.batch_size == 4


def test_video_input_defaults():
    inp = videos.GenerateVideoInput(prompt="a flying kite")
    assert inp.aspect_ratio == "16:9"
    assert inp.max_wait_seconds == 600


def test_speech_speed_bounds():
    with pytest.raises(ValidationError):
        audio.GenerateSpeechInput(text="hi", speed=99.0)


def test_list_models_default_relevant_only():
    assert account.ListModelsInput().relevant_only is True
