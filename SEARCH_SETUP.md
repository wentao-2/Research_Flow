# 🔍 ResearchFlow 搜索配置指南

## 推荐方案：Tavily (与 EvoScientist 相同)

### 1. 注册 Tavily

访问 https://tavily.com 注册账号，获取 **API Key**

- 免费版：每月 1000 次搜索
- 付费版：更多额度和高级功能

### 2. 配置 API Key

```bash
# 编辑 .env 文件
cd /ext/ResearchFlow
vim .env
```

添加：
```bash
TAVILY_API_KEY=tvly-your-api-key-here
```

### 3. 安装依赖 (可选，如果尚未安装)

```bash
pip install tavily-python httpx markdownify
```

### 4. 验证配置

```bash
cd /ext/ResearchFlow
python3 -c "
import asyncio
from tools.search_tool import WebSearchTool

tool = WebSearchTool()
print(f'搜索后端: {tool.backend}')

async def test():
    result = await tool.execute(query='federated learning', num_results=3)
    print(result.content[:1000])

asyncio.run(test())
"
```

---

## 备选方案

### 方案 B: DuckDuckGo (免费，无需 API Key)

```bash
# 安装依赖
pip install duckduckgo-search

# 确保 .env 中没有 TAVILY_API_KEY
# 或注释掉
```

**缺点**：偶尔网络不稳定，无法获取某些网页内容

### 方案 C: Brave Search (通过 MCP)

```bash
# 使用 MCP 添加 Brave Search
cd /ext/ResearchFlow

# 添加 MCP 配置
mkdir -p ~/.config/researchflow
cat > ~/.config/researchflow/mcp.json << 'EOF'
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    }
  }
}
EOF
```

获取 Brave API Key: https://brave.com/search/api/

---

## 🔧 搜索工具对比

| 特性 | Tavily | DuckDuckGo | Brave |
|------|--------|-----------|-------|
| 需要 API Key | ✅ | ❌ | ✅ |
| 费用 | 免费额度 | 免费 | 免费额度 |
| AI 总结 | ✅ | ❌ | ❌ |
| 获取网页内容 | ✅ | ❌ | ✅ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 📋 快速检查清单

- [ ] 注册 Tavily 账号 (https://tavily.com)
- [ ] 获取 API Key
- [ ] 编辑 `.env` 文件添加 `TAVILY_API_KEY`
- [ ] 重启 ResearchFlow
- [ ] 测试搜索功能

---

## 🐛 故障排除

### 问题: "搜索后端: mock"
```bash
# 检查环境变量是否加载
cd /ext/ResearchFlow
python3 -c "import os; print(os.environ.get('TAVILY_API_KEY', 'Not set'))"

# 手动加载 .env
export $(grep -v '^#' .env | xargs)
```

### 问题: "连接超时"
- 检查网络连接
- 尝试使用代理
- 切换到 DuckDuckGo 后端

### 问题: "API Key 无效"
- 检查 Key 是否复制完整
- 确认 Tavily 账号状态
- 检查是否有免费额度剩余
