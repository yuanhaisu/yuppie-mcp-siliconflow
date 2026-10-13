"""视频生成工具：submit_video_generation / get_video_status / generate_video"""

from __future__ import annotations

from pydantic import BaseModel, Field
from yuppie_siliconflow import VIDEO_SIZES

from ._client import get_client

_ASPECTS = " / ".join(VIDEO_SIZES)


class SubmitVideoInput(BaseModel):
    """submit_video_generation 入参。"""

    prompt: str = Field(..., min_length=1, description="视频提示词")
    model: str | None = Field(None, description="模型，默认 Wan-AI/Wan2.2-T2V-A14B")
    aspect_ratio: str = Field("16:9", description=f"宽高比，可选：{_ASPECTS}")
    negative_prompt: str | None = Field(None, description="负面提示词")
    seed: int | None = Field(None, ge=0, description="随机种子")


class VideoStatusInput(BaseModel):
    """get_video_status 入参。"""

    request_id: str = Field(..., min_length=1, description="submit 返回的 requestId")


class GenerateVideoInput(BaseModel):
    """generate_video 入参。"""

    prompt: str = Field(..., min_length=1, description="视频提示词")
    model: str | None = Field(None, description="模型，默认 Wan-AI/Wan2.2-T2V-A14B")
    aspect_ratio: str = Field("16:9", description=f"宽高比，可选：{_ASPECTS}")
    polling_interval: int = Field(15, ge=1, le=60, description="轮询间隔秒数")
    max_wait_seconds: int = Field(600, ge=30, le=3600, description="最长等待秒数")


async def submit_video_generation(inp: SubmitVideoInput) -> str:
    """提交视频生成任务，立即返回 requestId。"""
    try:
        client = get_client()
        request_id = await client.submit_video_generation(
            inp.prompt,
            model=inp.model,
            aspect_ratio=inp.aspect_ratio,
            negative_prompt=inp.negative_prompt,
            seed=inp.seed,
        )
        return f"✅ 视频任务已提交，requestId：`{request_id}`\n用 get_video_status 轮询进度。"
    except Exception as exc:  # noqa: BLE001
        return f"❌ 提交视频任务失败：{exc}"


async def get_video_status(inp: VideoStatusInput) -> str:
    """查询视频生成任务状态。"""
    try:
        client = get_client()
        status = await client.get_video_status(inp.request_id)
        if status["status"] == "Succeed":
            return f"✅ 生成成功：{status['url']}"
        if status["status"] == "Failed":
            return f"❌ 生成失败：{status.get('reason')}"
        return f"⏳ 状态：{status['status']}"
    except Exception as exc:  # noqa: BLE001
        return f"❌ 查询视频状态失败：{exc}"


async def generate_video(inp: GenerateVideoInput) -> str:
    """提交并轮询视频生成，直到完成/失败/超时。"""
    try:
        client = get_client()
        result = await client.generate_video(
            inp.prompt,
            model=inp.model,
            aspect_ratio=inp.aspect_ratio,
            polling_interval=inp.polling_interval,
            max_wait_seconds=inp.max_wait_seconds,
        )
        if result["status"] == "Succeed":
            lines = [f"✅ 视频生成成功（requestId：{result['request_id']}）"]
            if result.get("local_path"):
                lines.append(f"- 本地文件：`{result['local_path']}`")
            lines.append(f"- 在线视频：{result['url']}")
            return "\n".join(lines)
        if result["status"] == "Failed":
            return f"❌ 视频生成失败：{result.get('reason')}"
        return (
            f"⏳ 视频仍在生成中（requestId：{result['request_id']}），"
            f"请稍后用 get_video_status 再次查询。"
        )
    except Exception as exc:  # noqa: BLE001
        return f"❌ 生成视频失败：{exc}"
