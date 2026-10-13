"""账户信息与模型列表工具：get_user_info / list_models"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ._client import get_client


class ListModelsInput(BaseModel):
    """list_models 入参。"""

    relevant_only: bool = Field(True, description="仅返回图像/视频/语音相关模型")


async def get_user_info() -> str:
    """查询硅基流动账户信息与余额。"""
    try:
        client = get_client()
        info = await client.get_user_info()
        return (
            "✅ 账户信息：\n"
            f"- ID：{info['id']}\n"
            f"- 名称：{info['name']}\n"
            f"- 邮箱：{info['email']}\n"
            f"- 总余额：$ {info['total_balance']}\n"
            f"- 充值余额：$ {info['charge_balance']}\n"
            f"- 赠送余额：$ {info['free_balance']}\n"
            f"- 账户状态：{info['status']}"
        )
    except Exception as exc:  # noqa: BLE001
        return f"❌ 查询账户信息失败：{exc}"


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
