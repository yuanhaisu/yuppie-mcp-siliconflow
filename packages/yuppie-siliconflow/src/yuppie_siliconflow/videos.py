"""文生视频（SiliconFlow /v1/video/submit 与 /v1/video/status）"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .files import download_file

VIDEO_SIZES: dict[str, str] = {
    "16:9": "1280x720",
    "9:16": "720x1280",
    "1:1": "960x960",
}

DEFAULT_VIDEO_MODEL = "Wan-AI/Wan2.2-T2V-A14B"


class VideosMixin:
    """视频生成能力。"""

    _config: Any
    _request: Any
    _raise_for_status: Any

    async def submit_video_generation(
        self,
        prompt: str,
        *,
        model: str | None = None,
        aspect_ratio: str = "16:9",
        negative_prompt: str | None = None,
        seed: int | None = None,
    ) -> str:
        """提交视频生成任务，返回 requestId。"""
        use_model = model or DEFAULT_VIDEO_MODEL
        payload: dict[str, Any] = {
            "model": use_model,
            "prompt": prompt,
            "image_size": VIDEO_SIZES.get(aspect_ratio, "1280x720"),
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        resp = await self._request("POST", "/v1/video/submit", json=payload)
        self._raise_for_status(resp, "提交视频任务")
        request_id = resp.json().get("requestId")
        if not request_id:
            raise RuntimeError("SiliconFlow 未返回 requestId")
        return str(request_id)

    async def get_video_status(self, request_id: str) -> dict[str, Any]:
        """查询视频任务状态，返回 ``{"status", "url", "reason"}``。"""
        resp = await self._request(
            "POST", "/v1/video/status", json={"requestId": request_id}
        )
        self._raise_for_status(resp, "查询视频状态")

        data = resp.json()
        status = data.get("status")
        url: str | None = None
        if status == "Succeed":
            videos = (data.get("results") or {}).get("videos") or []
            if videos:
                url = videos[0].get("url")
        return {"status": status, "url": url, "reason": data.get("reason")}

    async def generate_video(
        self,
        prompt: str,
        *,
        model: str | None = None,
        aspect_ratio: str = "16:9",
        polling_interval: int = 15,
        max_wait_seconds: int = 600,
    ) -> dict[str, Any]:
        """提交并轮询视频生成，直到完成/失败/超时。"""
        request_id = await self.submit_video_generation(
            prompt, model=model, aspect_ratio=aspect_ratio
        )

        start = time.time()
        while time.time() - start < max_wait_seconds:
            status = await self.get_video_status(request_id)
            if status["status"] == "Succeed":
                url = status["url"]
                local_path: str | None = None
                if url and self._config.image_dir:
                    local_path = await download_file(url, self._config.image_dir, "video")
                return {
                    "request_id": request_id,
                    "status": "Succeed",
                    "url": url,
                    "local_path": local_path,
                }
            if status["status"] == "Failed":
                return {
                    "request_id": request_id,
                    "status": "Failed",
                    "reason": status["reason"],
                }
            await asyncio.sleep(polling_interval)

        return {"request_id": request_id, "status": "Timeout"}
