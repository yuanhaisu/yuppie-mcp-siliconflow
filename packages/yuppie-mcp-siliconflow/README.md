# yuppie-mcp-siliconflow

硅基流动（SiliconFlow）MCP Server — 让 AI 助手通过 MCP 协议生成图像。

## 特性

- **文生图** `generate_image`：支持宽高比 / 显式尺寸 / 种子 / 负面提示词 / 张数；返回 `<img>` 标签，AI 加 `width` 后可直接在对话里显示
- **图生图 / 编辑** `edit_image`：基于 URL 或 base64 图像按指令编辑
- **本地保存**：配置目录后自动把生成的图像落盘

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
| `SILICONFLOW_IMAGE_DIR` | | 图像保存目录 |

## 工具列表

| 工具 | 说明 |
|------|------|
| `generate_image` | 文生图 |
| `edit_image` | 图生图 / 编辑 |

## 注意事项

`FLUX.1-schnell` / `FLUX.1-dev` 在硅基流动返回的 S3 预签名 URL 签名无效，立即下载会
`403 SignatureDoesNotMatch`。默认模型因此改用 `Tongyi-MAI/Z-Image-Turbo`。
