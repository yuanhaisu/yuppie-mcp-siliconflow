# yuppie-siliconflow

硅基流动（SiliconFlow）API 客户端库：文生图 / 图生图 / 文生视频 / 语音合成 / 账户信息。

**纯客户端库，不含 MCP、不依赖 `mcp` 包**，可在任意 Python 项目中直接使用。

## 安装

```bash
uv pip install yuppie-siliconflow
# 或
pip install yuppie-siliconflow
```

## 快速开始

```python
import asyncio

from yuppie_siliconflow import SiliconFlowClient


async def main() -> None:
    client = SiliconFlowClient.from_env()  # 读取 SILICONFLOW_API_KEY
    result = await client.generate_image(
        prompt="a cozy reading nook, warm afternoon light, illustration",
        resolution="1024x1024",
    )
    print(result["images"][0]["url"])
    await client.aclose()


asyncio.run(main())
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SILICONFLOW_API_KEY` | ✅ | 硅基流动 API Key |
| `SILICONFLOW_BASE_URL` | | 默认 `https://api.siliconflow.com`（国内站改 `https://api.siliconflow.cn`） |
| `SILICONFLOW_MODEL` | | 默认文生图模型，默认 `Tongyi-MAI/Z-Image-Turbo` |
| `SILICONFLOW_IMAGE_DIR` | | 图片/视频保存目录，不设则只回传在线 URL |
| `SILICONFLOW_AUDIO_DIR` | | 音频保存目录，回退到 `SILICONFLOW_IMAGE_DIR` |

> 也可不依赖环境变量，直接构造：`SiliconFlowClient(SiliconFlowConfig(api_key="sk-..."))`。

## 能力

- `generate_image(...)` — 文生图（支持分辨率、宽高比、种子、负面提示词、批量）
- `edit_image(...)` — 图生图 / 图像编辑
- `submit_video_generation(...)` / `get_video_status(...)` / `generate_video(...)` — 文生视频
- `generate_speech(...)` — 语音合成
- `get_user_info()` — 账户信息 / 余额
- `list_models()` — 拉取可用模型列表

## 注意事项

`FLUX.1-schnell` / `FLUX.1-dev` 在硅基流动返回的 S3 预签名 URL 签名无效，生成后立即下载也会
`403 SignatureDoesNotMatch`。默认模型因此改用 `Tongyi-MAI/Z-Image-Turbo`；如需使用这两个模型，
建议开启本地保存（`SILICONFLOW_IMAGE_DIR`）以外的备用方案，或改用其它 FLUX 型号。
