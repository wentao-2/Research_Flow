"""
LLM 客户端 - 支持 Kimi Code API
"""
import json
import os
from typing import AsyncIterator, Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class Message:
    """消息类"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class StreamingChunk:
    """流式响应块"""
    content: str = ""
    thinking: str = ""
    tool_calls: Optional[List[Dict]] = None
    finish_reason: Optional[str] = None


class LLMClient:
    """LLM 客户端基类"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamingChunk]:
        """聊天接口"""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Anthropic/Kimi 客户端"""
    
    def __init__(self, api_key: str, base_url: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, base_url, model)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        except ImportError:
            print("⚠️  anthropic 库未安装，使用模拟模式")
            print("   安装: pip install anthropic")
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[Dict]]:
        """转换消息格式为 Anthropic 格式"""
        system_prompt = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                anthropic_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif msg.role == "tool":
                # 工具结果作为 user 消息
                anthropic_messages.append({
                    "role": "user",
                    "content": f"<tool_result>{msg.content}</tool_result>"
                })
        
        return system_prompt, anthropic_messages
    
    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """转换工具格式"""
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool.get("parameters", {}),
            })
        return anthropic_tools
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamingChunk]:
        """聊天接口"""
        if self.client is None:
            # 模拟模式
            yield StreamingChunk(
                content="⚠️ LLM 客户端未初始化。请安装 anthropic 库并配置 API Key。",
                finish_reason="stop"
            )
            return
        
        system, anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools) if tools else None
        
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or 8192,
                temperature=temperature,
                system=system or None,
                messages=anthropic_messages,
                tools=anthropic_tools,
            ) as stream:
                current_content = ""
                current_thinking = ""
                current_tool_calls = []
                
                async for event in stream:
                    if event.type == "content_block_delta":
                        delta = event.delta
                        
                        # 处理文本
                        if hasattr(delta, 'text') and delta.text:
                            current_content += delta.text
                            yield StreamingChunk(content=delta.text)
                        
                        # 处理 thinking
                        if hasattr(delta, 'thinking') and delta.thinking:
                            current_thinking += delta.thinking
                            yield StreamingChunk(thinking=delta.thinking)
                        
                        # 处理工具调用参数累积
                        if hasattr(delta, 'partial_json') and delta.partial_json:
                            if current_tool_calls:
                                current_tool_calls[-1]["arguments"] += delta.partial_json
                    
                    elif event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_calls.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "arguments": "",
                            })
                    
                    elif event.type == "message_stop":
                        # 解析工具调用参数
                        for tc in current_tool_calls:
                            if tc["arguments"]:
                                try:
                                    tc["arguments"] = json.loads(tc["arguments"])
                                except json.JSONDecodeError:
                                    tc["arguments"] = {}
                            else:
                                tc["arguments"] = {}
                        
                        # 检查是否有完整工具调用
                        if current_tool_calls:
                            yield StreamingChunk(
                                tool_calls=current_tool_calls,
                                finish_reason="tool_calls"
                            )
                        else:
                            yield StreamingChunk(finish_reason="stop")
                        
        except Exception as e:
            yield StreamingChunk(
                content=f"❌ LLM 错误: {str(e)}",
                finish_reason="error"
            )


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端（用于测试）"""
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamingChunk]:
        """模拟聊天"""
        yield StreamingChunk(
            content="这是一个模拟响应。请配置真实的 API Key 来使用 LLM。",
            finish_reason="stop"
        )


def create_llm_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    provider: str = "anthropic"
) -> LLMClient:
    """创建 LLM 客户端"""
    from .config import get_config
    
    config = get_config()
    api_key = api_key or config.api_key
    base_url = base_url or config.base_url
    model = model or config.model
    
    if not api_key:
        print("⚠️  API Key 未设置，使用模拟客户端")
        return MockLLMClient(api_key, base_url, model)
    
    if provider == "anthropic":
        return AnthropicClient(api_key, base_url, model)
    else:
        return MockLLMClient(api_key, base_url, model)
