"""
工具基类定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    content: str
    data: Optional[Dict] = None
    error: Optional[str] = None


class Tool(ABC):
    """工具基类"""
    
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于 LLM）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> list:
        """列出所有工具"""
        return list(self._tools.values())
    
    def to_dict_list(self) -> list:
        """转换为字典列表"""
        return [tool.to_dict() for tool in self._tools.values()]


# 全局工具注册表
_registry = ToolRegistry()


def register_tool(tool: Tool):
    """注册工具"""
    _registry.register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """获取工具"""
    return _registry.get(name)


def get_all_tools() -> list:
    """获取所有工具"""
    return _registry.list_tools()


def get_tools_dict() -> list:
    """获取工具字典列表"""
    return _registry.to_dict_list()
