"""按模型的分辨率解析测试（纯函数，不触网）"""

import pytest
from yuppie_siliconflow.images import MODEL_ASPECT_SIZES, resolve_image_size


@pytest.mark.parametrize(
    "model,aspect,expected",
    [
        # Z-Image 的推荐尺寸里没有 1024x1024，1:1 必须是 512x512
        ("Tongyi-MAI/Z-Image-Turbo", "1:1", "512x512"),
        ("Tongyi-MAI/Z-Image-Turbo", "16:9", "1024x576"),
        ("Tongyi-MAI/Z-Image-Turbo", "3:4", "768x1024"),
        # FLUX.2 系是 512 档
        ("black-forest-labs/FLUX.2-pro", "1:1", "512x512"),
        ("black-forest-labs/FLUX.2-pro", "4:3", "1024x768"),
        # Qwen-Image 是 1328 档大尺寸
        ("Qwen/Qwen-Image", "1:1", "1328x1328"),
        ("Qwen/Qwen-Image", "16:9", "1664x928"),
        # Ultra / dev 是 1024 档
        ("black-forest-labs/FLUX-1.1-pro-Ultra", "1:1", "1024x1024"),
        ("black-forest-labs/FLUX.1-dev", "3:4", "768x1024"),
        # 编辑模型沿用同族
        ("Qwen/Qwen-Image-Edit", "1:1", "1328x1328"),
    ],
)
def test_aspect_ratio_maps_per_model(model, aspect, expected):
    assert resolve_image_size(None, aspect, model) == expected


def test_explicit_image_size_wins_over_aspect_ratio():
    """显式尺寸优先级高于比例，且不被模型表改写。"""
    assert resolve_image_size("1376x768", "1:1", "Tongyi-MAI/Z-Image-Turbo") == "1376x768"


def test_unknown_model_falls_back_to_generic_table():
    assert resolve_image_size(None, "1:1", "some/new-model") == "1024x1024"
    assert resolve_image_size(None, "16:9", "some/new-model") == "1024x576"


def test_unknown_aspect_ratio_falls_back_to_model_default():
    assert resolve_image_size(None, "999:1", "Tongyi-MAI/Z-Image-Turbo") == "512x512"
    assert resolve_image_size(None, "999:1", "Qwen/Qwen-Image") == "1328x1328"


def test_no_model_no_aspect_ratio_uses_generic_default():
    assert resolve_image_size(None, None, None) == "1024x1024"


def test_every_model_table_covers_square():
    """每个模型的映射都必须覆盖 1:1，否则方形图会掉进兜底。"""
    for model, table in MODEL_ASPECT_SIZES.items():
        assert "1:1" in table, model


def test_model_tables_only_use_documented_sizes():
    """映射出的尺寸必须落在该模型文档给出的推荐值里。"""
    documented = {
        "Tongyi-MAI/Z-Image-Turbo": {"512x512", "768x1024", "1024x576", "576x1024"},
        "black-forest-labs/FLUX.2-pro": {
            "512x512", "768x1024", "1024x768", "576x1024", "1024x576",
        },
        "black-forest-labs/FLUX.2-flex": {
            "512x512", "768x1024", "1024x768", "576x1024", "1024x576",
        },
        "Qwen/Qwen-Image": {
            "1328x1328", "1664x928", "928x1664", "1472x1140", "1140x1472", "1584x1056", "1056x1584",
        },
        "Qwen/Qwen-Image-Edit": {
            "1328x1328", "1664x928", "928x1664", "1472x1140", "1140x1472", "1584x1056", "1056x1584",
        },
        "black-forest-labs/FLUX-1.1-pro-Ultra": {
            "1024x1024", "960x1280", "768x1024", "720x1440", "720x1280",
            # 文档的尺寸枚举含 others，允许枚举之外的尺寸
            "1024x768", "1280x720",
        },
        "black-forest-labs/FLUX.1-dev": {
            "1024x1024", "960x1280", "768x1024", "720x1440", "720x1280",
            "1024x768", "1280x720",
        },
        "black-forest-labs/FLUX.1-schnell": {
            "1024x1024", "512x1024", "768x512", "768x1024", "1024x576", "576x1024",
        },
        "black-forest-labs/FLUX-1.1-pro": {
            "1024x1024", "1024x768", "768x1024", "1280x720", "720x1280",
        },
    }
    for model, table in MODEL_ASPECT_SIZES.items():
        if model not in documented:
            continue
        for aspect, size in table.items():
            assert size in documented[model], f"{model} {aspect} → {size} 不在文档推荐值内"
