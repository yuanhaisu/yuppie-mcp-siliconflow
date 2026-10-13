"""库包客户端单例懒加载"""

from __future__ import annotations

from yuppie_siliconflow import SiliconFlowClient

_client: SiliconFlowClient | None = None


def get_client() -> SiliconFlowClient:
    """首次调用时读取环境变量构造客户端，后续复用。"""
    global _client
    if _client is None:
        _client = SiliconFlowClient.from_env()
    return _client
