"""SiliconFlow 客户端基类：httpx client、统一请求与错误格式化"""

from __future__ import annotations

from typing import Any

import httpx

from .config import SiliconFlowConfig


class SiliconFlowError(RuntimeError):
    """SiliconFlow API 调用失败。"""


class _SiliconFlowBase:
    """管理 httpx.AsyncClient 与 base_url/鉴权头。"""

    def __init__(self, config: SiliconFlowConfig, timeout: float = 120.0) -> None:
        self._config = config
        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

    @property
    def config(self) -> SiliconFlowConfig:
        return self._config

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._http

    async def aclose(self) -> None:
        """关闭底层连接池。"""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        client = self._client()
        try:
            return await client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:  # 网络层错误
            raise SiliconFlowError(f"请求 SiliconFlow 失败：{exc}") from exc

    @staticmethod
    def _format_error(resp: httpx.Response) -> str:
        """把非 200 响应整理成可读错误串。"""
        try:
            payload: Any = resp.json()
        except ValueError:
            payload = resp.text
        return f"HTTP {resp.status_code} - {payload}"

    def _raise_for_status(self, resp: httpx.Response, action: str) -> None:
        if resp.status_code != 200:
            raise SiliconFlowError(f"{action}失败：{self._format_error(resp)}")
