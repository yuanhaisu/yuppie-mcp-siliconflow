#!/bin/bash
# 本地调试脚本
#   默认：启动 MCP Inspector（浏览器 UI）
#   --cli：终端冒烟测试（initialize + tools/list）
#
# 用法：
#   bash scripts/debug.sh              # 浏览器调试
#   bash scripts/debug.sh --cli       # 终端冒烟测试
#   SILICONFLOW_API_KEY=sk-xxx bash scripts/debug.sh   # 临时注入 key
set -e

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 载入 .env（若存在），供 SILICONFLOW_API_KEY 等使用
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
    echo -e "${GREEN}✓ 已载入 .env${NC}"
fi

if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo -e "${YELLOW}⚠ 未设置 SILICONFLOW_API_KEY：tools/list 可用，但真实调用工具会返回失败${NC}"
    echo -e "${YELLOW}  提示：cp .env.example .env 并填入你的 Key${NC}"
fi

MODE="${1:-inspector}"

if [ "$MODE" = "--cli" ] || [ "$MODE" = "cli" ]; then
    echo -e "${GREEN}终端冒烟测试：initialize + tools/list${NC}"
    {
        printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"debug","version":"1"}}}'
        sleep 0.5
        printf '%s\n' '{"jsonrpc":"2.0","method":"notifications/initialized"}'
        sleep 0.5
        printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
        sleep 1.5
    } | uv run yuppie-mcp-siliconflow 2>/dev/null
    echo
    exit 0
fi

echo -e "${GREEN}启动 MCP Inspector（浏览器 UI）...${NC}"
echo -e "  打开终端输出的 http://127.0.0.1:6274?MCP_INSPECTOR_API_TOKEN=... 地址"
echo -e "  在 UI 里点 Connect → List Tools → 选工具 → 填参数 → Run"
exec npx -y @modelcontextprotocol/inspector uv run yuppie-mcp-siliconflow
