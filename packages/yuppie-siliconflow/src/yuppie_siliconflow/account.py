"""账户信息与模型列表（SiliconFlow /v1/user/info 与 /v1/models）"""

from __future__ import annotations

from typing import Any

# list_models 的过滤关键字
_RELEVANT_KEYWORDS = (
    "flux",
    "z-image",
    "stable-diffusion",
    "sd3",
    "sdxl",
    "kolors",
    "qwen-image",
    "wan",
    "i2v",
    "t2v",
    "speech",
    "tts",
    "cosyvoice",
    "indextts",
)


class AccountMixin:
    """账户与模型元信息。"""

    _request: Any
    _raise_for_status: Any

    async def get_user_info(self) -> dict[str, Any]:
        """查询账户信息与余额。"""
        resp = await self._request("GET", "/v1/user/info")
        self._raise_for_status(resp, "查询账户信息")

        body = resp.json()
        if not body.get("status", True):
            raise RuntimeError(f"SiliconFlow 返回失败：{body.get('message')}")

        data = body.get("data", {})
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "email": data.get("email"),
            "total_balance": data.get("totalBalance"),
            "charge_balance": data.get("chargeBalance"),
            "free_balance": data.get("balance"),
            "status": data.get("status"),
        }

    async def list_models(self, *, relevant_only: bool = True) -> list[str]:
        """拉取可用模型；默认只保留图像/视频/语音相关模型。"""
        resp = await self._request("GET", "/v1/models")
        self._raise_for_status(resp, "拉取模型列表")

        models = [m.get("id", "") for m in resp.json().get("data", [])]
        if not relevant_only:
            return [m for m in models if m]
        return [m for m in models if m and any(k in m.lower() for k in _RELEVANT_KEYWORDS)]
