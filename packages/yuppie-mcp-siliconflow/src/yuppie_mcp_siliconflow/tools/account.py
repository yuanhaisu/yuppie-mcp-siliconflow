"""模型列表工具：list_models"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ._client import get_client


class ListModelsInput(BaseModel):
    """list_models 入参。"""

    relevant_only: bool = Field(True, description="仅返回图像/视频/语音相关模型")


async def list_models(inp: ListModelsInput) -> str:
    """列出硅基流动可用模型。"""
    try:
        client = get_client()
        models = await client.list_models(relevant_only=inp.relevant_only)
        if not models:
            return "（未匹配到相关模型）"
        return "可用模型：\n" + "\n".join(f"- {m}" for m in models)
    except Exception as exc:  # noqa: BLE001
        return f"❌ 拉取模型列表失败：{exc}"
