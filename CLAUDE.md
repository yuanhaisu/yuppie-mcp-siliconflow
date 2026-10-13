# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

本仓库是 **uv workspace 双包**结构：

| 包 | 分发 | 职责 |
|----|------|------|
| `packages/yuppie-siliconflow` | PyPI（`pip install yuppie-siliconflow`） | 纯 SiliconFlow API 客户端库，**无 MCP、无 pydantic 依赖**（deps 仅 httpx），版本独立演进 |
| `packages/yuppie-mcp-siliconflow` | PyPI（`uvx yuppie-mcp-siliconflow`），依赖 `yuppie-siliconflow>=x.y` | MCP 壳：server.py 把库能力注册为 MCP 工具 |

拆分动机：只想调用硅基流动 API 的用户，不被强制安装 `mcp>=2.0.0,<3.0.0`（避免与其自身项目的 MCP 版本冲突）。

## 开发命令

```bash
# 安装开发依赖（workspace 双包 + dev extras）
uv sync --all-packages --all-extras

# 运行测试
uv run pytest -v

# 代码检查
uv run ruff check packages/ tests/
uv run mypy packages/*/src

# 本地运行 MCP Server（stdio 模式）
SILICONFLOW_API_KEY=sk-xxx uv run yuppie-mcp-siliconflow

# 构建双包（uv build 一次只接受一个 SRC）
uv build packages/yuppie-siliconflow
uv build packages/yuppie-mcp-siliconflow
```

## 架构设计

### 库包 `packages/yuppie-siliconflow/src/yuppie_siliconflow/`

- **`__init__.py`**：`__version__` + `SiliconFlowClient`（mixin 聚合类）+ re-export 常量与配置
- **`config.py`**：`SiliconFlowConfig`（dataclass），`from_env()` 读取并校验 `SILICONFLOW_API_KEY`，内置轻量 `.env` 加载（无第三方依赖）
- **`base.py`**：`_SiliconFlowBase` —— httpx client、`_request`、`_format_error`、`_raise_for_status`；`SiliconFlowError`
- **`files.py`**：`fetch_bytes`（裸 client 取字节，供内联）/ `guess_image_format` / `download_file` / `save_binary_file`（模块级函数，无 client）
- **`images.py`** — `ImagesMixin`：`generate_image` / `edit_image`；含 `RESOLUTIONS`、`ASPECT_RATIOS`（通用比例表）、`MODEL_ASPECT_SIZES`（各模型的比例 → 尺寸）、`resolve_image_size`

库方法返回结构化 `dict`，API 失败抛 `SiliconFlowError`（或 `RuntimeError`）。

### 壳包 `packages/yuppie-mcp-siliconflow/src/yuppie_mcp_siliconflow/`

- **`tools/`**：MCP 工具层（Pydantic BaseModel 入参 + async 实现），**不 import mcp**；产出中性结果对象
  `ImageToolResult`（文本摘要 + `ImageData` 字节），跨包引用库包；`_client.py` 提供模块级单例懒加载
- **`server.py`**：唯一 import mcp 的文件。`MCPServer` 注册 2 个工具，参数用 `Annotated[type, Field(...)]`；
  `_to_content()` 把 `ImageToolResult` 转成 `list[TextContent | Image]`

### 传输模式

默认 stdio；设 `MCP_TRANSPORT=streamable-http` 时走 HTTP。

## 代码规范

- `ruff`（line-length = 100）+ `mypy`（strict = true），配置在根 `pyproject.toml`
- 工具参数通过 Pydantic BaseModel 校验
- 工具返回 `list[TextContent | Image]`（文本摘要 + 原生图片块）；失败时只返回一条
  `❌ ...失败：{异常}` 的 `TextContent`
- 图片以**原生 MCP `ImageContent` 块**回传（服务端 `fetch_bytes` 下载字节内联），
  **不要**再拼 `<img>` 标签或把签名 URL 当图片交给前端 —— 见「已知坑」

## 添加新工具

1. 在库包对应 mixin 上加 API 薄包装方法（返回 dict）
2. 在壳包 `tools/<域>.py` 加 BaseModel + async 实现（引用库包 client）
3. 在壳包 `server.py` 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated[type, Field(...)]`
4. 在 `tests/` 加校验测试

## 已知坑

`FLUX.1-schnell` / `FLUX.1-dev` 返回的 S3 预签名 URL 签名无效（403），默认模型用
`Tongyi-MAI/Z-Image-Turbo`，由 `SILICONFLOW_MODEL` 覆盖。

图片**不要**回传临时签名 URL 让前端渲染：

- 曾用「返回 `<img>` 标签、模型补 `width`」的形态，在 Cherry Studio 里显示为破图
  （URL 经 `curl` 实测 200/真 PNG，是 raw HTML 的 `src` 过不了前端 sanitize 管线）。
  现改为服务端 `fetch_bytes` 下载字节、工具返回原生 `ImageContent` 块。
- 取字节必须用**裸** httpx client（不带 `Authorization`）：S3 只允许一种鉴权机制，
  与 URL 里的 `X-Amz-*` 同时出现会 403。
- `mimeType` 必须是 `image/png` —— S3 常回 `application/octet-stream`，
  客户端靠 mimeType 决定渲不渲染。

各模型的尺寸档位不同（512 档 / 1328 档 / 1024 档），比例到尺寸的映射**必须按模型查**
`MODEL_ASPECT_SIZES`，不能用一张全局表 —— 默认模型 Z-Image 的推荐集里就没有 `1024x1024`。

账户信息接口 `/v1/user/info` 已被硅基流动于 2026-08-14 永久下线（HTTP 410）；`list_models`
也随工具面收敛一并移除，故库包不再有 `AccountMixin`。
