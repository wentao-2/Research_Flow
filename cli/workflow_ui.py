"""
工作流 UI 组件
"""
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from core.workflow import ResearchWorkflow, WorkflowStage


class WorkflowUI:
    """工作流 UI 管理"""
    
    def __init__(self, console: Console):
        self.console = console
        self.workflow: Optional[ResearchWorkflow] = None
    
    def create_workflow(self, llm_client=None, tools=None) -> ResearchWorkflow:
        """创建工作流"""
        self.workflow = ResearchWorkflow(llm_client=llm_client, tools=tools)
        
        # 设置回调
        self.workflow.on_stage_change = self._on_stage_change
        self.workflow.on_message = self._on_message
        
        return self.workflow
    
    def _on_stage_change(self, stage: WorkflowStage):
        """阶段变更回调"""
        icons = {
            WorkflowStage.IDLE: "⏸️",
            WorkflowStage.UNDERSTANDING: "📝",
            WorkflowStage.PLANNING: "📋",
            WorkflowStage.LITERATURE: "📚",
            WorkflowStage.CODING: "💻",
            WorkflowStage.EXPERIMENT: "🧪",
            WorkflowStage.ANALYSIS: "📊",
            WorkflowStage.WRITING: "✍️",
            WorkflowStage.REVIEW: "👀",
            WorkflowStage.COMPLETED: "✅",
        }
        icon = icons.get(stage, "▶️")
        self.console.print(f"\n{icon} 进入阶段: {stage.value}", style="bold cyan")
    
    def _on_message(self, message: str):
        """消息回调"""
        self.console.print(f"  {message}", style="dim")
    
    def show_status(self):
        """显示工作流状态"""
        if not self.workflow:
            self.console.print("⚠️ 工作流未启动", style="yellow")
            return
        
        status = self.workflow.get_status()
        
        table = Table(title="📊 工作流状态")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")
        
        table.add_row("当前阶段", status["stage"])
        table.add_row("研究主题", status["topic"] or "N/A")
        table.add_row("进度", f"{status['progress']:.1f}%")
        
        self.console.print(table)
        
        # 显示计划
        if status["plan"]:
            self.console.print("\n📋 研究计划:", style="bold")
            for i, task in enumerate(status["plan"], 1):
                done = task in status["completed"]
                symbol = "✅" if done else "⬜"
                self.console.print(f"  {symbol} {i}. {task}")
    
    async def run_full_workflow(self, topic: str):
        """运行完整工作流"""
        if not self.workflow:
            self.console.print("❌ 请先创建工作流", style="red")
            return
        
        self.console.print(Panel(
            f"开始研究工作流\n主题: {topic}",
            title="🔬 ResearchFlow",
            border_style="blue"
        ))
        
        # 运行工作流
        await self.workflow.run(topic)
        
        # 显示结果
        self.console.print("\n" + "="*60, style="green")
        self.console.print("✅ 工作流完成！", style="bold green")
        
        # 显示报告
        if "report" in self.workflow.state.artifacts:
            self.console.print("\n📄 研究报告:")
            self.console.print(self.workflow.state.artifacts["report"])
    
    async def run_single_step(self, step: str, **kwargs):
        """运行单步任务"""
        if not self.workflow:
            self.console.print("❌ 请先创建工作流", style="red")
            return
        
        step_names = {
            "literature": "文献调研",
            "code": "代码实现",
            "experiment": "实验执行",
            "writing": "报告撰写",
        }
        
        name = step_names.get(step, step)
        self.console.print(f"\n🔧 执行: {name}", style="bold cyan")
        
        result = await self.workflow.run_step(step, **kwargs)
        
        self.console.print(f"\n📤 结果:")
        self.console.print(result[:1000] if len(result) > 1000 else result)
