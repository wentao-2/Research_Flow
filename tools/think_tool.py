"""
思考工具 - 让 Agent 可以显式思考
"""
from .base import Tool, ToolResult, register_tool


class ThinkTool(Tool):
    """思考工具"""
    
    name = "think"
    description = """使用此工具来思考复杂问题。当你需要：
- 分析问题并制定计划
- 评估多个选项
- 检查推理过程中的错误
- 总结关键信息
- 决定下一步行动时
使用此工具来整理思路。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "thought": {
                "type": "string",
                "description": "你的思考过程"
            }
        },
        "required": ["thought"]
    }
    
    async def execute(self, thought: str, **kwargs) -> ToolResult:
        """记录思考过程"""
        # 这个工具实际上不执行任何操作，只是让 LLM 有机会显式思考
        return ToolResult(
            success=True,
            content=f"💭 思考: {thought[:200]}..." if len(thought) > 200 else f"💭 思考: {thought}",
            data={"thought": thought}
        )


class TodoTool(Tool):
    """待办事项工具"""
    
    name = "todo"
    description = "管理待办事项列表"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "操作: add, list, done, clear",
                "enum": ["add", "list", "done", "clear"]
            },
            "content": {
                "type": "string",
                "description": "待办事项内容（add 时使用）",
                "default": ""
            },
            "index": {
                "type": "integer",
                "description": "待办事项索引（done 时使用）",
                "default": 0
            }
        },
        "required": ["action"]
    }
    
    _todos = []
    
    async def execute(self, action: str, content: str = "", index: int = 0, **kwargs) -> ToolResult:
        if action == "add":
            self._todos.append({"content": content, "done": False})
            return ToolResult(
                success=True,
                content=f"✅ 已添加待办: {content}",
                data={"todos": self._todos}
            )
        
        elif action == "list":
            if not self._todos:
                return ToolResult(success=True, content="📋 待办列表为空")
            
            lines = ["📋 待办事项:"]
            for i, todo in enumerate(self._todos, 1):
                status = "✅" if todo["done"] else "⬜"
                lines.append(f"{status} {i}. {todo['content']}")
            return ToolResult(success=True, content="\n".join(lines), data={"todos": self._todos})
        
        elif action == "done":
            if 0 < index <= len(self._todos):
                self._todos[index-1]["done"] = True
                return ToolResult(
                    success=True,
                    content=f"✅ 已完成: {self._todos[index-1]['content']}"
                )
            return ToolResult(success=False, content="", error="无效的索引")
        
        elif action == "clear":
            self._todos.clear()
            return ToolResult(success=True, content="🗑️ 已清空待办列表")
        
        return ToolResult(success=False, content="", error="未知操作")


# 注册工具
register_tool(ThinkTool())
register_tool(TodoTool())
