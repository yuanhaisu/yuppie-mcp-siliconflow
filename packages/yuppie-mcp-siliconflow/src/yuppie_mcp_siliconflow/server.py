"""SiliconFlow MCP Server 主入口"""

from __future__ import annotations

import os
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .tools import account, audio, images, videos

mcp = MCPServer(
    name="siliconflow_mcp",
    instructions=(
        "硅基流动（SiliconFlow）生成工具集：文生图、图生图/编辑、文生视频、语音合成，"
        "以及账户余额查询与模型列表。默认文生图模型为 Tongyi-MAI/Z-Image-Turbo。"
    ),
    version=__version__,
)


# ═══════════════════════════════════════════
# 图片工具
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
    resolution: Annotated[
        str | None,
        Field(description="显式分辨率，如 1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280"),
    ] = None,
    aspect_ratio: Annotated[
        str | None, Field(description="宽高比：1:1 / 3:4 / 4:3 / 9:16 / 16:9")
    ] = None,
    model: Annotated[
        str | None,
        Field(description="模型 ID；不填用 SILICONFLOW_MODEL 或默认 Tongyi-MAI/Z-Image-Turbo"),
    ] = None,
    seed: Annotated[int | None, Field(description="随机种子，用于复现", ge=0)] = None,
    negative_prompt: Annotated[str | None, Field(description="负面提示词")] = None,
    batch_size: Annotated[int, Field(description="生成张数（1-4）", ge=1, le=4)] = 1,
    output_format: Annotated[str, Field(description="输出格式：png / jpeg")] = "png",
) -> str:
    """根据提示词生成图像。

    返回中包含一个 `<img>` 标签：请为其添加 `width` 属性（200~500 像素）
    后原样发送给用户，以便直接显示图片。"""
    return await images.generate_image(
        images.GenerateImageInput(
            prompt=prompt,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            model=model,
            seed=seed,
            negative_prompt=negative_prompt,
            batch_size=batch_size,
            output_format=output_format,
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
        str | None, Field(description="编辑模型，默认 Qwen/Qwen-Image-Edit-2509")
    ] = None,
) -> str:
    """基于已有图像按指令编辑。"""
    return await images.edit_image(
        images.EditImageInput(image=image, prompt=prompt, model=model)
    )


# ═══════════════════════════════════════════
# 视频工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="submit_video_generation",
    annotations=ToolAnnotations(
        title="提交视频生成任务",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_submit_video_generation(
    prompt: Annotated[str, Field(description="视频提示词", min_length=1)],
    model: Annotated[
        str | None, Field(description="模型，默认 Wan-AI/Wan2.2-T2V-A14B")
    ] = None,
    aspect_ratio: Annotated[str, Field(description="宽高比：16:9 / 9:16 / 1:1")] = "16:9",
    negative_prompt: Annotated[str | None, Field(description="负面提示词")] = None,
    seed: Annotated[int | None, Field(description="随机种子", ge=0)] = None,
) -> str:
    """提交视频生成任务，立即返回 requestId。"""
    return await videos.submit_video_generation(
        videos.SubmitVideoInput(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            seed=seed,
        )
    )


# ✅
@mcp.tool(
    name="get_video_status",
    annotations=ToolAnnotations(
        title="查询视频生成状态",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_video_status(
    request_id: Annotated[str, Field(description="submit 返回的 requestId", min_length=1)],
) -> str:
    """查询视频生成任务状态。"""
    return await videos.get_video_status(videos.VideoStatusInput(request_id=request_id))


# ✅
@mcp.tool(
    name="generate_video",
    annotations=ToolAnnotations(
        title="生成视频（自动轮询）",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_generate_video(
    prompt: Annotated[str, Field(description="视频提示词", min_length=1)],
    model: Annotated[
        str | None, Field(description="模型，默认 Wan-AI/Wan2.2-T2V-A14B")
    ] = None,
    aspect_ratio: Annotated[str, Field(description="宽高比：16:9 / 9:16 / 1:1")] = "16:9",
    polling_interval: Annotated[int, Field(description="轮询间隔秒数", ge=1, le=60)] = 15,
    max_wait_seconds: Annotated[
        int, Field(description="最长等待秒数", ge=30, le=3600)
    ] = 600,
) -> str:
    """提交并轮询视频生成，直到完成/失败/超时。"""
    return await videos.generate_video(
        videos.GenerateVideoInput(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            polling_interval=polling_interval,
            max_wait_seconds=max_wait_seconds,
        )
    )


# ═══════════════════════════════════════════
# 语音工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="generate_speech",
    annotations=ToolAnnotations(
        title="文字转语音",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_generate_speech(
    text: Annotated[str, Field(description="要合成的文本", min_length=1)],
    model: Annotated[
        str | None,
        Field(
            description=(
                "模型：fishaudio/fish-speech-1.5 / IndexTeam/IndexTTS-2 / "
                "FunAudioLLM/CosyVoice2-0.5B"
            )
        ),
    ] = None,
    voice: Annotated[
        str | None, Field(description="嗓音 ID，如 fishaudio/fish-speech-1.5:alex")
    ] = None,
    response_format: Annotated[str, Field(description="音频格式：mp3 / opus / wav / pcm")] = "mp3",
    sample_rate: Annotated[int, Field(description="采样率", ge=8000, le=48000)] = 32000,
    speed: Annotated[float, Field(description="语速倍率", ge=0.1, le=3.0)] = 1.0,
    gain: Annotated[float, Field(description="音量增益 dB", ge=-10.0, le=10.0)] = 0.0,
) -> str:
    """文本转语音。配置了音频目录则落盘，否则回传 base64。"""
    return await audio.generate_speech(
        audio.GenerateSpeechInput(
            text=text,
            model=model,
            voice=voice,
            response_format=response_format,
            sample_rate=sample_rate,
            speed=speed,
            gain=gain,
        )
    )


# ═══════════════════════════════════════════
# 账户工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="get_user_info",
    annotations=ToolAnnotations(
        title="查询账户信息",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_user_info() -> str:
    """查询硅基流动账户信息与余额。"""
    return await account.get_user_info()


# ✅
@mcp.tool(
    name="list_models",
    annotations=ToolAnnotations(
        title="列出可用模型",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_list_models(
    relevant_only: Annotated[
        bool, Field(description="仅返回图像/视频/语音相关模型")
    ] = True,
) -> str:
    """列出硅基流动可用模型。"""
    return await account.list_models(account.ListModelsInput(relevant_only=relevant_only))


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
