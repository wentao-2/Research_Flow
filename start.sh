#!/bin/bash
# ResearchFlow 启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🔬 ResearchFlow 启动器${NC}"
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 需要安装 Python 3${NC}"
    exit 1
fi

# 加载环境变量
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${BLUE}📄 加载环境配置...${NC}"
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# 检查 API Key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  警告: ANTHROPIC_API_KEY 未设置${NC}"
    echo "   请在 .env 文件中设置 API Key"
    echo ""
fi

# 启动 CLI
echo -e "${GREEN}🚀 启动 ResearchFlow...${NC}"
echo ""
cd "$SCRIPT_DIR" && python3 ./researchflow
