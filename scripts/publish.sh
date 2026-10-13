#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 双包结构：库包 yuppie-siliconflow（PyPI）+ 壳包 yuppie-mcp-siliconflow（PyPI，依赖库包）
LIB_PKG_DIR="packages/yuppie-siliconflow"
SHELL_PKG_DIR="packages/yuppie-mcp-siliconflow"
LIB_PYPROJECT="${LIB_PKG_DIR}/pyproject.toml"
LIB_INIT="${LIB_PKG_DIR}/src/yuppie_siliconflow/__init__.py"
SHELL_PYPROJECT="${SHELL_PKG_DIR}/pyproject.toml"
SHELL_INIT="${SHELL_PKG_DIR}/src/yuppie_mcp_siliconflow/__init__.py"

echo -e "${GREEN}=== PyPI 发布脚本（库包 + 壳包）===${NC}"

# ── 选择动作（可多选）──
echo -e "这次要做什么？（可多选，逗号分隔；回车默认 4=全部）"
echo -e "  1) 发布壳包 yuppie-mcp-siliconflow"
echo -e "  2) 发布库包 yuppie-siliconflow"
echo -e "  3) 仅打 tag v<壳包版本> 并推送"
echo -e "  4) 全部（发布壳包 + 发布库包 + 打 tag）"
read -p "选择: " ACTIONS
if [ -z "$ACTIONS" ] || [ "$ACTIONS" = "4" ]; then
    DO_SHELL=1; DO_LIB=1; DO_TAG=1
else
    DO_SHELL=0; DO_LIB=0; DO_TAG=0
    IFS=',' read -ra SEL <<< "$ACTIONS"
    for a in "${SEL[@]}"; do
        case "$a" in
            1) DO_SHELL=1 ;;
            2) DO_LIB=1 ;;
            3) DO_TAG=1 ;;
            *) echo -e "${RED}未知选项: $a${NC}"; exit 1 ;;
        esac
    done
fi

if [ "$DO_SHELL" = "0" ] && [ "$DO_LIB" = "0" ] && [ "$DO_TAG" = "0" ]; then
    echo -e "${RED}未选择任何动作${NC}"; exit 1
fi

# 检查 token（有发布动作就需要）
if { [ "$DO_SHELL" = "1" ] || [ "$DO_LIB" = "1" ]; } && [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${RED}错误: 未设置 UV_PUBLISH_TOKEN 环境变量${NC}"
    echo "请设置 PyPI API Token:"
    echo "  export UV_PUBLISH_TOKEN='pypi-你的token'"
    exit 1
fi

# ── 版本输入（只问选中的包）──
CURRENT_SHELL=$(grep '^version = ' "${SHELL_PYPROJECT}" | sed 's/version = "\(.*\)"/\1/')
CURRENT_LIB=$(grep '^version = ' "${LIB_PYPROJECT}" | sed 's/version = "\(.*\)"/\1/')
NEW_SHELL="$CURRENT_SHELL"
NEW_LIB="$CURRENT_LIB"

if [ "$DO_SHELL" = "1" ]; then
    read -p "壳包新版本号 (当前: ${CURRENT_SHELL}): " v
    [ -n "$v" ] && NEW_SHELL="$v"
fi
if [ "$DO_LIB" = "1" ]; then
    read -p "库包新版本号 (当前: ${CURRENT_LIB}): " v
    [ -n "$v" ] && NEW_LIB="$v"
fi
if [ "$DO_TAG" = "1" ] && [ "$DO_SHELL" = "0" ]; then
    read -p "tag 版本号 v<版本> (壳包当前: ${CURRENT_SHELL}): " v
    [ -n "$v" ] && NEW_SHELL="$v"
fi

# ── 确认 ──
echo -e "${YELLOW}即将执行:${NC}"
[ "$DO_SHELL" = "1" ] && echo "  发布壳包 yuppie-mcp-siliconflow ${NEW_SHELL}"
[ "$DO_LIB" = "1" ] && echo "  发布库包 yuppie-siliconflow ${NEW_LIB}"
[ "$DO_TAG" = "1" ] && echo "  打 tag v${NEW_SHELL}"
read -p "确认? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消${NC}"
    exit 1
fi

# ── 版本 bump + 提交（确认后才改，取消不产生任何改动）──
[ "$DO_SHELL" = "1" ] && [ "$NEW_SHELL" != "$CURRENT_SHELL" ] && {
    sed -i '' "s/^version = .*/version = \"${NEW_SHELL}\"/" "${SHELL_PYPROJECT}"
    sed -i '' "s/__version__ = .*/__version__ = \"${NEW_SHELL}\"/" "${SHELL_INIT}"
}
[ "$DO_LIB" = "1" ] && [ "$NEW_LIB" != "$CURRENT_LIB" ] && {
    sed -i '' "s/^version = .*/version = \"${NEW_LIB}\"/" "${LIB_PYPROJECT}"
    sed -i '' "s/__version__ = .*/__version__ = \"${NEW_LIB}\"/" "${LIB_INIT}"
}
git add "${SHELL_PYPROJECT}" "${SHELL_INIT}" "${LIB_PYPROJECT}" "${LIB_INIT}"
if ! git diff --cached --quiet; then
    git commit -q -m "chore: bump 版本（壳包 ${NEW_SHELL} + 库包 ${NEW_LIB}）"
    echo -e "${GREEN}✓ 版本 bump 已提交${NC}"
fi

# 发布保护：选中的包版本不得与已发布的重复（PyPI 会 403）
if [ "$DO_SHELL" = "1" ]; then
    if curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/yuppie-mcp-siliconflow/${NEW_SHELL}/json" | grep -q 200; then
        echo -e "${RED}错误: 壳包 ${NEW_SHELL} 已发布到 PyPI，无法重复发布${NC}"
        git restore --staged --worktree "${SHELL_PYPROJECT}" "${SHELL_INIT}" 2>/dev/null
        exit 1
    fi
fi
if [ "$DO_LIB" = "1" ]; then
    if curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/yuppie-siliconflow/${NEW_LIB}/json" | grep -q 200; then
        echo -e "${RED}错误: 库包 ${NEW_LIB} 已发布到 PyPI，无法重复发布${NC}"
        git restore --staged --worktree "${LIB_PYPROJECT}" "${LIB_INIT}" 2>/dev/null
        exit 1
    fi
fi

# ── 构建 + 发布：库包先发（壳包依赖它）──
rm -rf dist/
if [ "$DO_LIB" = "1" ]; then
    echo -e "${GREEN}构建库包...${NC}"
    uv build "${LIB_PKG_DIR}"
    echo -e "${GREEN}发布库包...${NC}"
    UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish dist/yuppie_siliconflow-*
fi
if [ "$DO_SHELL" = "1" ]; then
    echo -e "${GREEN}构建壳包...${NC}"
    uv build "${SHELL_PKG_DIR}"
    echo -e "${GREEN}发布壳包...${NC}"
    UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish dist/yuppie_mcp_siliconflow-*
fi

# ── tag（选中时；与壳包版本对齐）──
if [ "$DO_TAG" = "1" ]; then
    TAG="v${NEW_SHELL}"
    echo -e "${GREEN}正在处理 tag ${TAG} ...${NC}"
    if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
        echo -e "${YELLOW}tag ${TAG} 已存在，跳过${NC}"
    else
        read -p "创建并推送 tag ${TAG}（壳包 ${NEW_SHELL} + 库包 ${NEW_LIB}）? (Y/n): " TAG_CONFIRM
        if [[ ! "$TAG_CONFIRM" =~ ^[Nn]$ ]]; then
            git tag -a "${TAG}" -m "yuppie-mcp-siliconflow ${NEW_SHELL} + yuppie-siliconflow ${NEW_LIB}"
            git push origin "${TAG}"
            echo -e "${GREEN}✓ tag ${TAG} 已推送${NC}"
        else
            echo -e "${YELLOW}已跳过 tag${NC}"
        fi
    fi
fi

echo -e "${GREEN}=== 完成 ===${NC}"
[ "$DO_SHELL" = "1" ] && echo -e "${GREEN}  https://pypi.org/project/yuppie-mcp-siliconflow/${NC}"
[ "$DO_LIB" = "1" ] && echo -e "${GREEN}  https://pypi.org/project/yuppie-siliconflow/${NC}"
