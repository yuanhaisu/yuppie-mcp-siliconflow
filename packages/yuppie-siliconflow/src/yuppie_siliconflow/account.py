"""模型列表（SiliconFlow /v1/models）

注：账户信息接口 /v1/user/info 已被硅基流动于 2026-08-14 永久下线（HTTP 410），
且官方尚未提供替代接口，故不再提供账户查询能力。
"""

from __future__ import annotations

from typing import Any

# list_models 的过滤关键字（图像模型）
_RELEVANT_KEYWORDS = (
    "flux",
    "z-image",
    "stable-diffusion",
    "sd3",
    "sdxl",
    "kolors",
    "qwen-image",
)


class AccountMixin:
    """模型元信息。"""

    _request: Any
    _raise_for_status: Any

    async def list_models(self, *, relevant_only: bool = True) -> list[str]:
        """拉取可用模型；默认只保留图像相关模型。"""
        resp = await self._request("GET", "/v1/models")
        self._raise_for_status(resp, "拉取模型列表")

        models = [m.get("id", "") for m in resp.json().get("data", [])]
        if not relevant_only:
            return [m for m in models if m]
        return [m for m in models if m and any(k in m.lower() for k in _RELEVANT_KEYWORDS)]
