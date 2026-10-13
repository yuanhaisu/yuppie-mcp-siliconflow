# yuppie-mcp-siliconflow

硅基流动（SiliconFlow）MCP Server — 让 AI 助手通过 MCP 协议生成图像、视频与语音。

## 特性

- **文生图** `generate_image`：支持分辨率 / 宽高比 / 种子 / 负面提示词 / 批量；返回 `<img>` 标签，AI 加 `width` 后可直接在对话里显示
- **图生图 / 编辑** `edit_image`：基于 URL 或 base64 图像按指令编辑
- **文生视频** `generate_video` / `submit_video_generation` / `get_video_status`：自动轮询
- **语音合成** `generate_speech`：fish-speech / IndexTTS / CosyVoice
- **模型列表** `list_models`：列出可用模型
- **本地保存**：配置目录后自动把图像/视频/音频落盘

## 架构说明

本包是 MCP 壳：核心客户端代码在库包 `yuppie-siliconflow`（PyPI 分发，`pip install yuppie-siliconflow`），本包依赖它。
如只需在 Python 项目里调用硅基流动 API（不要 MCP），直接装库包即可。

## 快速开始

### 准备 API Key

在 [硅基流动控制台](https://cloud.siliconflow.com/account/ak)（国际站）申请 API Key。

### Claude Code

```bash
claude mcp add siliconflow \
  -e SILICONFLOW_API_KEY="sk-你的Key" \
  -e SILICONFLOW_IMAGE_DIR="/path/to/save/images" \
  -- uvx yuppie-mcp-siliconflow
```

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "siliconflow": {
      "command": "uvx",
      "args": ["yuppie-mcp-siliconflow"],
      "env": {
        "SILICONFLOW_API_KEY": "sk-你的Key",
        "SILICONFLOW_IMAGE_DIR": "/path/to/save/images"
      }
    }
  }
}
```

### opencode

```jsonc
{
  "mcp": {
    "siliconflow": {
      "type": "local",
      "command": ["uvx", "yuppie-mcp-siliconflow"],
      "environment": { "SILICONFLOW_API_KEY": "sk-你的Key" }
    }
  }
}
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SILICONFLOW_API_KEY` | ✅ | API Key |
| `SILICONFLOW_BASE_URL` | | 默认 `https://api.siliconflow.com`（国内站 `https://api.siliconflow.cn`） |
| `SILICONFLOW_MODEL` | | 默认文生图模型，默认 `Tongyi-MAI/Z-Image-Turbo` |
| `SILICONFLOW_IMAGE_DIR` | | 图像/视频保存目录 |
| `SILICONFLOW_AUDIO_DIR` | | 音频保存目录（回退到 `IMAGE_DIR`） |

## 工具列表

| 工具 | 说明 |
|------|------|
| `generate_image` | 文生图 |
| `edit_image` | 图生图 / 编辑 |
| `submit_video_generation` | 提交视频任务，返回 requestId |
| `get_video_status` | 查询视频任务状态 |
| `generate_video` | 提交并轮询视频生成 |
| `generate_speech` | 文字转语音 |
| `list_models` | 列出可用模型 |

## 注意事项

`FLUX.1-schnell` / `FLUX.1-dev` 在硅基流动返回的 S3 预签名 URL 签名无效，立即下载会
`403 SignatureDoesNotMatch`。默认模型因此改用 `Tongyi-MAI/Z-Image-Turbo`。
