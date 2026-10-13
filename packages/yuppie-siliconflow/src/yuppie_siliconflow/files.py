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
    ".mp4",
    ".webm",
    ".mp3",
    ".wav",
    ".opus",
    ".flac",
)


def _guess_extension(url: str, default: str = ".png") -> str:
    path = url.lower().split("?", 1)[0]
    for ext in _KNOWN_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return default


async def download_file(url: str, save_dir: str, prefix: str = "gen") -> str:
    """下载远程文件到本地目录，返回本地绝对路径；下载失败时原样返回 URL。"""
    try:
        target = Path(save_dir).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        ext = _guess_extension(url)
        file_path = target / f"{prefix}_{int(time.time() * 1000)}{ext}"
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            file_path.write_bytes(resp.content)
        return str(file_path.resolve())
    except Exception as exc:  # noqa: BLE001 - 下载只是增强，失败不应中断主流程
        print(f"[yuppie-siliconflow] 下载失败，返回原始 URL：{exc}")
        return url


def save_binary_file(
    content: bytes,
    save_dir: str,
    extension: str = "mp3",
    prefix: str = "audio",
) -> str:
    """把二进制内容写入本地目录，返回本地绝对路径。"""
    target = Path(save_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{prefix}_{int(time.time() * 1000)}.{extension}"
    file_path.write_bytes(content)
    return str(file_path.resolve())
