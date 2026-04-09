"""
研究工作流系统
协调多个 Agent 完成复杂研究任务
"""
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class WorkflowStage(Enum):
    """工作流阶段"""
    IDLE = "idle"
    UNDERSTANDING = "understanding"  # 理解需求
    PLANNING = "planning"            # 制定计划
    LITERATURE = "literature"        # 文献调研
    CODING = "coding"                # 代码实现
    EXPERIMENT = "experiment"        # 实验执行
    ANALYSIS = "analysis"            # 结果分析
    WRITING = "writing"              # 报告撰写
    REVIEW = "review"                # 审查
    COMPLETED = "completed"          # 完成


@dataclass
class WorkflowState:
    """工作流状态"""
    current_stage: WorkflowStage = WorkflowStage.IDLE
    topic: str = ""
    plan: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


class ResearchWorkflow:
    """
    研究工作流
    
    自动协调多个 Agent 完成研究任务：
    1. 理解用户需求
    2. 制定研究计划
    3. 文献调研
    4. 代码实现
    5. 实验执行
    6. 结果分析
    7. 报告撰写
    """
    
    def __init__(self, llm_client=None, tools=None):
        self.llm_client = llm_client
        self.tools = tools or []
        self.state = WorkflowState()
        self.agents = {}
        
        # 回调
        self.on_stage_change: Optional[Callable[[WorkflowStage], None]] = None
        self.on_task_complete: Optional[Callable[[str], None]] = None
        self.on_message: Optional[Callable[[str], None]] = None
    
    def _emit(self, message: str):
        """发送消息"""
        if self.on_message:
            self.on_message(message)
    
    def _change_stage(self, stage: WorkflowStage):
        """切换阶段"""
        self.state.current_stage = stage
        if self.on_stage_change:
            self.on_stage_change(stage)
    
    async def run(self, topic: str) -> WorkflowState:
        """
        运行完整工作流
        
        Args:
            topic: 研究主题
        """
        self.state.topic = topic
        
        # 阶段 1: 理解需求
        await self._stage_understanding()
        
        # 阶段 2: 制定计划
        await self._stage_planning()
        
        # 阶段 3: 文献调研
        await self._stage_literature()
        
        # 阶段 4: 代码实现
        await self._stage_coding()
        
        # 阶段 5: 实验执行
        await self._stage_experiment()
        
        # 阶段 6: 报告撰写
        await self._stage_writing()
        
        self._change_stage(WorkflowStage.COMPLETED)
        return self.state
    
    async def run_step(self, step: str, **kwargs) -> str:
        """执行单步任务"""
        if step == "literature":
            return await self._do_literature_review(**kwargs)
        elif step == "code":
            return await self._do_code_implementation(**kwargs)
        elif step == "experiment":
            return await self._do_experiment(**kwargs)
        elif step == "writing":
            return await self._do_writing(**kwargs)
        else:
            return f"未知步骤: {step}"
    
    async def _stage_understanding(self):
        """理解需求阶段"""
        self._change_stage(WorkflowStage.UNDERSTANDING)
        self._emit(f"📝 理解研究需求: {self.state.topic}")
        
        # 这里可以添加更多需求分析逻辑
        self.state.context["topic"] = self.state.topic
        self.state.completed_tasks.append("需求理解")
    
    async def _stage_planning(self):
        """制定计划阶段"""
        self._change_stage(WorkflowStage.PLANNING)
        self._emit("📋 制定研究计划...")
        
        # 生成默认计划
        self.state.plan = [
            "文献调研 - 搜索相关研究",
            "代码实现 - 编写核心算法",
            "实验设计 - 设计验证实验",
            "结果分析 - 分析实验结果",
            "报告撰写 - 撰写研究文档",
        ]
        
        self.state.completed_tasks.append("计划制定")
    
    async def _stage_literature(self):
        """文献调研阶段"""
        self._change_stage(WorkflowStage.LITERATURE)
        self._emit("📚 开始文献调研...")
        
        # 使用 web_search 工具
        from tools.base import get_tool
        search_tool = get_tool("web_search")
        
        if search_tool:
            result = await search_tool.execute(
                query=self.state.topic,
                num_results=5
            )
            self.state.artifacts["literature"] = result.content
            self._emit("✅ 文献调研完成")
        
        self.state.completed_tasks.append("文献调研")
    
    async def _stage_coding(self):
        """代码实现阶段"""
        self._change_stage(WorkflowStage.CODING)
        self._emit("💻 准备代码实现...")
        
        # 这里可以添加代码生成逻辑
        self._emit("✅ 代码框架已准备")
        
        self.state.completed_tasks.append("代码实现")
    
    async def _stage_experiment(self):
        """实验执行阶段"""
        self._change_stage(WorkflowStage.EXPERIMENT)
        self._emit("🧪 准备实验执行...")
        
        # 这里可以添加实验执行逻辑
        self._emit("✅ 实验方案已设计")
        
        self.state.completed_tasks.append("实验执行")
    
    async def _stage_writing(self):
        """报告撰写阶段"""
        self._change_stage(WorkflowStage.WRITING)
        self._emit("📝 准备报告撰写...")
        
        # 汇总所有成果
        summary = f"""# 研究报告: {self.state.topic}

## 完成情况
"""
        for task in self.state.completed_tasks:
            summary += f"- [x] {task}\n"
        
        summary += f"\n## 文献调研\n{self.state.artifacts.get('literature', 'N/A')[:500]}..."
        
        self.state.artifacts["report"] = summary
        self._emit("✅ 报告撰写完成")
        
        self.state.completed_tasks.append("报告撰写")
    
    # 单步任务方法
    
    async def _do_literature_review(self, query: str = None) -> str:
        """执行文献调研"""
        from tools.base import get_tool
        
        search_tool = get_tool("web_search")
        if search_tool:
            result = await search_tool.execute(
                query=query or self.state.topic,
                num_results=5
            )
            return result.content
        return "搜索工具不可用"
    
    async def _do_code_implementation(self, requirement: str = None) -> str:
        """执行代码实现"""
        return "代码实现功能待开发"
    
    async def _do_experiment(self, config: dict = None) -> str:
        """执行实验"""
        return "实验执行功能待开发"
    
    async def _do_writing(self, content: str = None) -> str:
        """执行写作"""
        return "写作功能待开发"
    
    def get_status(self) -> Dict:
        """获取工作流状态"""
        return {
            "stage": self.state.current_stage.value,
            "topic": self.state.topic,
            "plan": self.state.plan,
            "completed": self.state.completed_tasks,
            "progress": len(self.state.completed_tasks) / max(len(self.state.plan), 1) * 100,
        }
