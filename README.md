# yuppie-mcp-siliconflow

硅基流动（SiliconFlow）MCP Server —— 让 AI 助手通过 MCP 协议生成**图像 / 视频 / 语音**。

合并自：

- [`lioensky/siliconflow-flux-mcp-server`](https://github.com/lioensky/siliconflow-flux-mcp-server)（TypeScript 生图 MCP）
- [`stevefordev/siliconflow-mcp`](https://github.com/stevefordev/siliconflow-mcp)（Python 多模态 MCP）

## 特性

- **文生图**：`prompt` + 分辨率 / 宽高比 / 种子 / 负面提示词 / 批量，返回 `<img>` 标签
- **图生图 / 编辑**
- **文生视频**：提交 + 自动轮询
- **语音合成**：fish-speech / IndexTTS / CosyVoice
- **账户工具**：余额查询、模型列表
- **本地保存**：图像 / 视频 / 音频自动落盘

## 双包结构

| 包 | 分发 | 职责 |
|----|------|------|
| `packages/yuppie-siliconflow` | PyPI（`pip install yuppie-siliconflow`） | 纯 API 客户端库，无 MCP 依赖 |
| `packages/yuppie-mcp-siliconflow` | PyPI（`uvx yuppie-mcp-siliconflow`） | MCP 壳，把库能力注册为工具 |

## 快速开始

```bash
# 直接用（推荐）
uvx yuppie-mcp-siliconflow

# 或本地开发
uv sync --all-packages --all-extras
uv run pytest -v
```

MCP 客户端配置（Claude Code / Desktop / opencode）见
[`packages/yuppie-mcp-siliconflow/README.md`](packages/yuppie-mcp-siliconflow/README.md)。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SILICONFLOW_API_KEY` | ✅ | API Key |
| `SILICONFLOW_BASE_URL` | | 默认 `https://api.siliconflow.com`（国内站 `https://api.siliconflow.cn`） |
| `SILICONFLOW_MODEL` | | 默认文生图模型，默认 `Tongyi-MAI/Z-Image-Turbo` |
| `SILICONFLOW_IMAGE_DIR` | | 图像/视频保存目录 |
| `SILICONFLOW_AUDIO_DIR` | | 音频保存目录（回退到 `IMAGE_DIR`） |

## 开发命令

```bash
uv sync --all-packages --all-extras
uv run pytest -v
uv run ruff check packages/ tests/
uv run mypy packages/*/src
```

## 发布

```bash
export UV_PUBLISH_TOKEN='pypi-你的token'
bash scripts/publish.sh
```

## 注意事项

`FLUX.1-schnell` / `FLUX.1-dev` 在硅基流动返回的 S3 预签名 URL 签名无效，立即下载会
`403 SignatureDoesNotMatch`。默认模型因此改用 `Tongyi-MAI/Z-Image-Turbo`，可用
`SILICONFLOW_MODEL` 覆盖。

## License

MIT
