"""生成结果落盘：下载远程文件 / 保存二进制内容"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

_KNOWN_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
)

# 扩展名 → MCP ``Image(format=...)`` 能识别的格式名
_EXT_TO_FORMAT = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".webp": "webp",
    ".gif": "gif",
}


def _guess_extension(url: str, default: str = ".png") -> str:
    path = url.lower().split("?", 1)[0]
    for ext in _KNOWN_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return default


def guess_image_format(url: str, default: str = "png") -> str:
    """从 URL 扩展名推断图片格式名（``png`` / ``jpeg`` / ``webp`` / ``gif``）。

    SiliconFlow 回传的 S3 URL 形如 ``..._00001_.png?X-Amz-...``，扩展名位于 query 之前。
    """
    return _EXT_TO_FORMAT.get(_guess_extension(url, f".{default}"), default)


async def fetch_bytes(url: str, timeout: float = 120.0) -> bytes:
    """下载远程文件并返回字节。

    必须使用**裸** ``httpx.AsyncClient``：S3 预签名 URL 只允许一种鉴权机制，
    若复用带 ``Authorization`` 头的业务 client，会与 URL 内的 ``X-Amz-*`` 冲突而报 403。
    失败时抛 ``httpx.HTTPError``，由调用方决定是否降级。
    """
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def download_file(url: str, save_dir: str, prefix: str = "gen") -> str:
    """下载远程文件到本地目录，返回本地绝对路径；下载失败时原样返回 URL。"""
    try:
        content = await fetch_bytes(url)
        extension = _guess_extension(url).lstrip(".")
        return save_binary_file(content, save_dir, extension, prefix)
    except Exception as exc:  # noqa: BLE001 - 下载只是增强，失败不应中断主流程
        print(f"[yuppie-siliconflow] 下载失败，返回原始 URL：{exc}")
        return url


def save_binary_file(
    content: bytes,
    save_dir: str,
    extension: str = "bin",
    prefix: str = "file",
) -> str:
    """把二进制内容写入本地目录，返回本地绝对路径。"""
    target = Path(save_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{prefix}_{int(time.time() * 1000)}.{extension}"
    file_path.write_bytes(content)
    return str(file_path.resolve())
