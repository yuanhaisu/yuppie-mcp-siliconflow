"""语音合成工具：generate_speech"""

from __future__ import annotations

from pydantic import BaseModel, Field
from yuppie_siliconflow import SPEECH_MODELS

from ._client import get_client


class GenerateSpeechInput(BaseModel):
    """generate_speech 入参。"""

    text: str = Field(..., min_length=1, description="要合成的文本")
    model: str | None = Field(
        None, description=f"模型，可选：{' / '.join(SPEECH_MODELS)}"
    )
    voice: str | None = Field(None, description="嗓音 ID，如 fishaudio/fish-speech-1.5:alex")
    response_format: str = Field("mp3", description="音频格式：mp3 / opus / wav / pcm")
    sample_rate: int = Field(32000, ge=8000, le=48000, description="采样率")
    speed: float = Field(1.0, ge=0.1, le=3.0, description="语速倍率")
    gain: float = Field(0.0, ge=-10.0, le=10.0, description="音量增益 dB")


async def generate_speech(inp: GenerateSpeechInput) -> str:
    """文本转语音。配置了音频目录则落盘，否则回传 base64。"""
    try:
        client = get_client()
        result = await client.generate_speech(
            inp.text,
            model=inp.model,
            voice=inp.voice,
            response_format=inp.response_format,
            sample_rate=inp.sample_rate,
            speed=inp.speed,
            gain=inp.gain,
        )
        if result.get("local_path"):
            return f"✅ 语音已生成：`{result['local_path']}`"
        return (
            f"✅ 语音已生成（{result['format']}，base64）：\n"
            f"```\n{result['audio_base64']}\n```"
        )
    except Exception as exc:  # noqa: BLE001
        return f"❌ 语音合成失败：{exc}"
