"""
ResearchFlow 交互式 CLI
参考 EvoScientist 和 Claude Code 的设计
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

# 导入核心组件
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.llm_client import create_llm_client
from tools.base import get_all_tools
from agents.base_agent import AgentMessage
from agents.research_agents import create_agent
from .workflow_ui import WorkflowUI


class ResearchFlowCLI:
    """ResearchFlow 交互式 CLI"""
    
    def __init__(self):
        self.console = Console()
        self.config = get_config()
        self.llm_client = None
        self.agent = None
        self.tools = get_all_tools()
        self.session_id = "default"
        self.workflow_ui = WorkflowUI(self.console)
        
        # 历史记录
        self.history: List[Dict] = []
        
    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╭──────────────────────────────────────────────────────────────╮
│                                                              │
│   🔬 ResearchFlow - 智能研究助手                            │
│                                                              │
│   基于 Kimi Code Plan API 的多 Agent 研究系统               │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
        """
        self.console.print(banner, style="bold blue")
        
        # 显示配置信息
        info = Text()
        info.append(f"  模型: ", style="dim")
        info.append(f"{self.config.model}\n", style="cyan")
        info.append(f"  工作目录: ", style="dim")
        info.append(f"{self.config.workspace_dir}\n", style="cyan")
        info.append(f"  可用工具: ", style="dim")
        info.append(f"{len(self.tools)} 个\n", style="cyan")
        info.append(f"\n  输入 /help 查看帮助，/exit 退出\n", style="yellow")
        
        self.console.print(info)
    
    def init_agent(self):
        """初始化 Agent"""
        if not self.config.validate():
            return False
        
        try:
            self.llm_client = create_llm_client(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                model=self.config.model,
            )
            
            self.agent = create_agent(
                "research",
                llm_client=self.llm_client,
                tools=self.tools,
            )
            
            # 初始化工作流
            self.workflow_ui.create_workflow(
                llm_client=self.llm_client,
                tools=self.tools,
            )
            
            return True
            
        except Exception as e:
            self.console.print(f"❌ 初始化失败: {e}", style="red")
            return False
    
    def print_help(self):
        """打印帮助"""
        help_text = """
## 可用命令

### 基础命令
- `/help` - 显示此帮助
- `/exit` 或 `/quit` - 退出
- `/clear` - 清空屏幕
- `/new` - 开始新会话

### Agent 切换
- `/agent research` - 研究助手（默认）
- `/agent literature` - 文献调研专家
- `/agent code` - 代码实现专家
- `/agent experiment` - 实验设计专家
- `/agent writing` - 学术写作专家

### 工作流命令
- `/workflow <主题>` - 运行完整研究工作流
- `/step <步骤>` - 运行单步任务 (literature/code/experiment/writing)
- `/status` - 查看工作流状态

### 工具命令
- `/tools` - 列出所有工具
- `/history` - 查看对话历史
- `/save <文件名>` - 保存会话

### 快捷操作
- `@filename` - 引用文件内容
- 直接输入问题开始对话

### 工作流
直接描述你的研究需求，我会自动协调多个 Agent 帮你完成：
- 文献调研
- 代码实现
- 实验设计
- 报告撰写
        """
        self.console.print(Markdown(help_text))
    
    def list_tools(self):
        """列出工具"""
        from rich.table import Table
        
        table = Table(title="🔧 可用工具")
        table.add_column("名称", style="cyan")
        table.add_column("描述", style="white")
        
        for tool in self.tools:
            desc = tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
            table.add_row(tool.name, desc)
        
        self.console.print(table)
    
    def switch_agent(self, agent_type: str):
        """切换 Agent"""
        try:
            self.agent = create_agent(
                agent_type,
                llm_client=self.llm_client,
                tools=self.tools,
            )
            self.console.print(f"✅ 已切换到 {agent_type} Agent", style="green")
        except Exception as e:
            self.console.print(f"❌ 切换失败: {e}", style="red")
    
    async def handle_command(self, command: str) -> bool:
        """处理命令，返回是否继续"""
        cmd = command.strip().lower()
        parts = command.strip().split(maxsplit=1)
        
        if cmd in ["/exit", "/quit", "/q"]:
            self.console.print("\n👋 再见！", style="green")
            return False
        
        elif cmd == "/help":
            self.print_help()
        
        elif cmd == "/clear":
            self.console.clear()
            self.print_banner()
        
        elif cmd == "/new":
            if self.agent:
                self.agent.clear_history()
            self.workflow_ui = WorkflowUI(self.console)
            self.workflow_ui.create_workflow(
                llm_client=self.llm_client,
                tools=self.tools,
            )
            self.console.print("🆕 已开启新会话", style="green")
        
        elif cmd == "/tools":
            self.list_tools()
        
        elif cmd == "/history":
            self.show_history()
        
        elif cmd == "/status":
            self.workflow_ui.show_status()
        
        elif cmd.startswith("/agent "):
            if len(parts) >= 2:
                agent_type = parts[1].strip()
                self.switch_agent(agent_type)
            else:
                self.console.print("❌ 用法: /agent <类型>", style="red")
        
        elif cmd.startswith("/save "):
            if len(parts) >= 2:
                filename = parts[1].strip()
                self.save_session(filename)
            else:
                self.console.print("❌ 用法: /save <文件名>", style="red")
        
        elif cmd.startswith("/workflow "):
            if len(parts) >= 2:
                topic = parts[1].strip()
                await self.workflow_ui.run_full_workflow(topic)
            else:
                self.console.print("❌ 用法: /workflow <研究主题>", style="red")
        
        elif cmd.startswith("/step "):
            if len(parts) >= 2:
                step = parts[1].strip()
                await self.workflow_ui.run_single_step(step)
            else:
                self.console.print("❌ 用法: /step <步骤名>", style="red")
        
        else:
            self.console.print(f"❓ 未知命令: {command}", style="red")
            self.console.print("输入 /help 查看帮助", style="dim")
        
        return True
    
    def show_history(self):
        """显示历史"""
        if not self.agent or not self.agent.message_history:
            self.console.print("📭 没有历史记录", style="dim")
            return
        
        for msg in self.agent.message_history[-10:]:
            if msg.role == "user":
                self.console.print(f"\n[blue]❯[/blue] {msg.content[:100]}...")
            elif msg.role == "assistant":
                self.console.print(f"[green]🤖[/green] {msg.content[:100]}...")
    
    def save_session(self, filename: str):
        """保存会话"""
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.config.memory_dir / filename
        
        data = {
            "session_id": self.session_id,
            "history": [
                {"role": m.role, "content": m.content}
                for m in (self.agent.message_history if self.agent else [])
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.console.print(f"💾 会话已保存: {filepath}", style="green")
    
    async def process_message(self, message: str):
        """处理用户消息"""
        if not self.agent:
            self.console.print("❌ Agent 未初始化", style="red")
            return
        
        # 处理文件引用 (@filename)
        if '@' in message:
            message = await self._resolve_file_mentions(message)
        
        # 显示思考中的指示器
        thinking_text = ""
        response_text = ""
        
        # 创建状态显示
        status_text = Text("🤔 思考中...")
        
        with Live(Spinner("dots", text="🤔 思考中..."), refresh_per_second=10, console=self.console) as live:
            try:
                async for resp in self.agent.chat(
                    message,
                    on_thinking=lambda t: live.update(Spinner("dots", text=f"💭 {t[:80]}...")),
                ):
                    if resp.content:
                        response_text += resp.content
            except Exception as e:
                self.console.print(f"❌ 对话错误: {e}", style="red")
                return
        
        # 打印响应
        if response_text:
            self.console.print(Markdown(response_text))
    
    async def _resolve_file_mentions(self, message: str) -> str:
        """解析文件引用"""
        import re
        
        pattern = r'@([\w\-_./]+)'
        matches = re.findall(pattern, message)
        
        for filename in matches:
            filepath = Path(filename)
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 替换为文件内容
                    placeholder = f"\n[文件: {filename}]\n```\n{content[:2000]}\n```\n"
                    message = message.replace(f"@{filename}", placeholder)
                except Exception as e:
                    message = message.replace(f"@{filename}", f"[无法读取文件: {filename}]")
            else:
                message = message.replace(f"@{filename}", f"[文件不存在: {filename}]")
        
        return message
    
    async def run(self):
        """运行 CLI"""
        self.print_banner()
        
        if not self.init_agent():
            self.console.print("\n⚠️  Agent 初始化失败，请检查配置", style="yellow")
            self.console.print("   编辑 .env 文件配置 API Key\n")
            return
        
        self.console.print("✅ Agent 初始化成功！\n", style="green")
        
        while True:
            try:
                # 获取输入
                user_input = input("\n\x1b[34;1m❯\x1b[0m ")
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # 检查是否是命令
                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue
                
                # 处理消息
                await self.process_message(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n\n⚠️  收到中断", style="yellow")
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"\n❌ 错误: {e}", style="red")
        
        self.console.print("\n👋 感谢使用 ResearchFlow!", style="bold green")


def main():
    """主函数"""
    cli = ResearchFlowCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
