# 🔬 ResearchFlow

智能研究助手 - 基于 Kimi Code Plan API 的多 Agent 研究系统

## 特性

- **多 Agent 架构** - 5 个专业 Agent 协作完成研究任务
  - ResearchAssistant: 研究助手（主协调者）
  - Literature: 文献调研专家
  - Code: 代码实现专家
  - Experiment: 实验设计专家
  - Writing: 学术写作专家

- **完整研究工作流**
  - 需求理解
  - 文献调研（集成网页搜索）
  - 代码实现
  - 实验执行
  - 报告撰写

- **丰富的工具集**
  - `bash` - 执行 shell 命令
  - `read_file`/`write_file` - 文件操作
  - `web_search` - 网页搜索
  - `fetch_url` - 获取网页内容
  - `think` - 显式思考
  - `todo` - 任务管理

- **交互式 CLI** - 类似 EvoScientist/Claude Code 的体验

## 快速开始

### 1. 配置环境

编辑 `.env` 文件：

```bash
# Kimi Code Plan API 配置
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://api.kimi.com/coding/

# 可选：搜索配置
# TAVILY_API_KEY=your-tavily-key
```

### 2. 启动

```bash
./start.sh
```

或

```bash
python3 researchflow
```

### 3. 使用

#### 直接对话
```
❯ 帮我调研大语言模型在代码生成中的自我纠错能力
```

#### 运行工作流
```
❯ /workflow 大语言模型代码生成研究
```

#### 运行单步任务
```
❯ /step literature
```

#### 切换 Agent
```
❯ /agent literature
```

#### 引用文件
```
❯ 请分析 @paper.md 的内容
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` | 退出 |
| `/new` | 新会话 |
| `/tools` | 列出工具 |
| `/agent <类型>` | 切换 Agent |
| `/workflow <主题>` | 运行工作流 |
| `/step <步骤>` | 运行单步 |
| `/status` | 查看状态 |
| `/history` | 查看历史 |
| `/save <文件>` | 保存会话 |
| `@文件名` | 引用文件 |

## 架构

```
ResearchFlow/
├── core/           # 核心模块
│   ├── config.py   # 配置管理
│   ├── llm_client.py  # LLM 客户端
│   └── workflow.py    # 工作流系统
├── agents/         # Agent 定义
│   ├── base_agent.py
│   └── research_agents.py
├── tools/          # 工具实现
│   ├── bash_tool.py
│   ├── file_tools.py
│   ├── search_tool.py
│   └── think_tool.py
├── cli/            # CLI 界面
│   ├── app.py      # 主应用
│   └── workflow_ui.py
├── memory/         # 记忆存储
├── workspace/      # 工作目录
└── researchflow    # 入口脚本
```

## 依赖

```bash
pip install anthropic rich aiohttp beautifulsoup4
```

可选依赖：
```bash
pip install duckduckgo-search  # 网页搜索
```

## 工作流示例

```
> /workflow "Transformer 模型在图像分类中的应用"

📝 理解研究需求...
📋 制定研究计划...
📚 开始文献调研...
   - 搜索相关论文
   - 分析现有方法
💻 准备代码实现...
🧪 准备实验执行...
📝 准备报告撰写...

✅ 工作流完成！
```

## 与其他工具对比

| 特性 | ResearchFlow | Claude Code | EvoScientist |
|------|-------------|-------------|--------------|
| API | Kimi Code | Anthropic | 多供应商 |
| 多 Agent | ✅ | ❌ | ✅ |
| 工作流 | ✅ | ❌ | ⚠️ |
| 网页搜索 | ✅ | ❌ | ✅ |
| 技能系统 | ⚠️ | ❌ | ✅ |
| 本地运行 | ✅ | ❌ | ✅ |

## License

MIT
