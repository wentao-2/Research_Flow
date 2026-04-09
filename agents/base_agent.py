"""
Agent 基类
"""
import json
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    """Agent 消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str
    thinking: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    finish_reason: str = "stop"


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm_client=None,
        tools: Optional[List] = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.tools = tools or []
        self.message_history: List[AgentMessage] = []
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[AgentResponse]:
        """
        与 Agent 对话
        
        Args:
            message: 用户消息
            context: 额外上下文
            on_thinking: 思考回调
            on_tool_call: 工具调用回调
        """
        # 添加用户消息
        self.message_history.append(AgentMessage(role="user", content=message))
        
        # 构建消息列表
        messages = self._build_messages(context)
        
        # 调用 LLM
        full_response = ""
        full_thinking = ""
        tool_calls = []
        
        if self.llm_client:
            from core.llm_client import Message
            
            llm_messages = [
                Message(role=m.role, content=m.content)
                for m in messages
            ]
            
            tools_dict = [t.to_dict() for t in self.tools] if self.tools else None
            
            async for chunk in self.llm_client.chat(
                messages=llm_messages,
                tools=tools_dict,
                stream=True,
            ):
                if chunk.content:
                    full_response += chunk.content
                    yield AgentResponse(content=chunk.content)
                
                if chunk.thinking:
                    full_thinking += chunk.thinking
                    if on_thinking:
                        on_thinking(chunk.thinking)
                
                if chunk.tool_calls:
                    tool_calls = chunk.tool_calls
                
                if chunk.finish_reason:
                    # 处理工具调用
                    if chunk.finish_reason == "tool_calls" and tool_calls:
                        for tc in tool_calls:
                            if on_tool_call:
                                on_tool_call(tc)
                            
                            # 执行工具
                            result = await self._execute_tool(tc)
                            
                            # 如果工具执行失败，添加错误信息到响应
                            if "错误" in result or "Error" in result:
                                yield AgentResponse(content=f"\n[工具调用错误: {result}]\n")
                            
                            # 添加工具调用和结果到历史
                            self.message_history.append(AgentMessage(
                                role="assistant",
                                content="",
                                tool_calls=[tc]
                            ))
                            self.message_history.append(AgentMessage(
                                role="tool",
                                content=result,
                                tool_call_id=tc.get("id")
                            ))
                        
                        # 限制递归深度，避免无限循环 (最多 200 轮对话)
                        if len(self.message_history) < 200:
                            async for resp in self.chat(
                                "",  # 空消息，继续对话
                                context,
                                on_thinking,
                                on_tool_call,
                            ):
                                yield resp
                        else:
                            yield AgentResponse(
                                content="\n[已达到最大对话深度 (200 轮)，请使用 /new 开始新会话]\n",
                                finish_reason="stop"
                            )
                    
                    else:
                        # 正常结束
                        self.message_history.append(AgentMessage(
                            role="assistant",
                            content=full_response
                        ))
                        yield AgentResponse(
                            content="",
                            thinking=full_thinking,
                            finish_reason=chunk.finish_reason
                        )
        else:
            # 模拟响应
            response = f"[{self.name}] 收到: {message[:50]}..."
            yield AgentResponse(content=response, finish_reason="stop")
    
    def _build_messages(self, context: Optional[Dict] = None) -> List[AgentMessage]:
        """构建消息列表"""
        messages = []
        
        # 系统提示
        if self.system_prompt:
            messages.append(AgentMessage(role="system", content=self.system_prompt))
        
        # 添加上下文
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append(AgentMessage(
                role="system",
                content=f"上下文信息:\n{context_str}"
            ))
        
        # 添加历史消息
        messages.extend(self.message_history)
        
        return messages
    
    async def _execute_tool(self, tool_call: Dict) -> str:
        """执行工具调用"""
        import inspect
        from tools.base import get_tool
        
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("arguments", {})
        
        # 解析参数
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except:
                tool_args = {}
        
        if not isinstance(tool_args, dict):
            tool_args = {}
        
        tool = get_tool(tool_name)
        if tool:
            try:
                # 获取工具的 execute 方法签名
                sig = inspect.signature(tool.execute)
                required_params = []
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    if param.default == inspect.Parameter.empty and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        required_params.append(param_name)
                
                # 检查必需参数
                missing_params = [p for p in required_params if p not in tool_args]
                if missing_params:
                    return f"工具调用错误: 缺少必需参数 {missing_params}"
                
                result = await tool.execute(**tool_args)
                return result.content if result.success else f"错误: {result.error}"
            except Exception as e:
                return f"工具执行错误: {str(e)}"
        else:
            return f"工具未找到: {tool_name}"
    
    def clear_history(self):
        """清除历史"""
        self.message_history.clear()
    
    def get_history(self) -> List[AgentMessage]:
        """获取历史"""
        return self.message_history.copy()
