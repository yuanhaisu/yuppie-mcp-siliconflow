"""语音合成（SiliconFlow /v1/audio/speech）"""

from __future__ import annotations

import base64
from typing import Any

from .files import save_binary_file

DEFAULT_SPEECH_MODEL = "fishaudio/fish-speech-1.5"
DEFAULT_VOICE = "fishaudio/fish-speech-1.5:alex"

SPEECH_MODELS = [
    "fishaudio/fish-speech-1.5",
    "IndexTeam/IndexTTS-2",
    "FunAudioLLM/CosyVoice2-0.5B",
]


class AudioMixin:
    """语音合成能力。"""

    _config: Any
    _request: Any
    _raise_for_status: Any

    async def generate_speech(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        response_format: str = "mp3",
        sample_rate: int = 32000,
        speed: float = 1.0,
        gain: float = 0.0,
    ) -> dict[str, Any]:
        """语音合成。

        返回 ``{"local_path", "audio_base64", "format"}``：
        配置了音频目录时落盘 ``local_path``；否则回传 ``audio_base64``。
        """
        use_model = model or DEFAULT_SPEECH_MODEL
        use_voice = voice or DEFAULT_VOICE
        # fish-speech 的嗓音需要带模型前缀
        if use_model == DEFAULT_SPEECH_MODEL and ":" not in use_voice:
            use_voice = f"{use_model}:{use_voice}"

        payload = {
            "model": use_model,
            "input": text,
            "voice": use_voice,
            "response_format": response_format,
            "sample_rate": sample_rate,
            "speed": speed,
            "gain": gain,
        }

        resp = await self._request("POST", "/v1/audio/speech", json=payload)
        self._raise_for_status(resp, "语音合成")

        content = resp.content
        if self._config.audio_dir:
            local_path = save_binary_file(
                content, self._config.audio_dir, extension=response_format, prefix="audio"
            )
            return {"local_path": local_path, "audio_base64": None, "format": response_format}

        return {
            "local_path": None,
            "audio_base64": base64.b64encode(content).decode("ascii"),
            "format": response_format,
        }
