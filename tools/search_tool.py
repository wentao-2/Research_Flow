"""
网页搜索工具
支持多种搜索后端: Tavily (推荐), DuckDuckGo, 或模拟模式
参考 EvoScientist 的实现
"""
import os
import json
from typing import Optional, List, Dict
from .base import Tool, ToolResult, register_tool


class WebSearchTool(Tool):
    """网页搜索工具"""
    
    name = "web_search"
    description = """搜索网页获取最新信息。用于：
- 查找最新的技术文档和 API 参考
- 搜索学术论文和研究资料 (arXiv, Google Scholar)
- 获取当前事件和新闻
- 验证事实和数据

此工具会搜索网页并返回相关结果的标题、URL 和内容摘要。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量 (默认 5, 最大 10)",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    def __init__(self):
        self.backend = self._detect_backend()
    
    def _detect_backend(self) -> str:
        """检测搜索后端"""
        if os.environ.get("TAVILY_API_KEY"):
            return "tavily"
        try:
            import duckduckgo_search
            return "duckduckgo"
        except ImportError:
            pass
        return "mock"
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """执行搜索"""
        # 限制结果数量
        num_results = min(max(num_results, 1), 10)
        
        if self.backend == "tavily":
            return await self._search_tavily(query, num_results)
        elif self.backend == "duckduckgo":
            return await self._search_duckduckgo(query, num_results)
        else:
            return await self._search_mock(query, num_results)
    
    async def _search_tavily(self, query: str, num_results: int) -> ToolResult:
        """使用 Tavily 搜索 (推荐)"""
        try:
            from tavily import TavilyClient
            import asyncio
            
            api_key = os.environ.get("TAVILY_API_KEY")
            if not api_key:
                return ToolResult(
                    success=False,
                    content="",
                    error="TAVILY_API_KEY 未设置"
                )
            
            client = TavilyClient(api_key=api_key)
            
            # 同步调用转为异步
            def _sync_search():
                return client.search(
                    query=query,
                    max_results=num_results,
                    search_depth="basic",  # 可选: basic, advanced
                    include_answer=True,
                )
            
            search_results = await asyncio.to_thread(_sync_search)
            
            results = search_results.get("results", [])
            answer = search_results.get("answer", "")
            
            # 格式化结果
            content = f"""🔍 搜索: {query}
{'='*60}
"""
            
            # AI 总结
            if answer:
                content += f"""
💡 AI 总结:
{answer}

"""
            
            # 搜索结果
            content += f"📚 找到 {len(results)} 个相关结果:\n"
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "无标题")
                url = result.get("url", "")
                snippet = result.get("content", "")[:500]
                score = result.get("score", 0)
                
                content += f"""
{i}. {title}
   🔗 {url}
   📄 {snippet}...
   ⭐ 相关度: {score:.2f}
"""
            
            return ToolResult(
                success=True,
                content=content,
                data={"results": results, "answer": answer, "query": query}
            )
            
        except ImportError:
            return ToolResult(
                success=False,
                content="",
                error="未安装 tavily-python。请运行: pip install tavily-python"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Tavily 搜索错误: {str(e)}")
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> ToolResult:
        """使用 DuckDuckGo 搜索 (免费备选)"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            
            if not results:
                return ToolResult(
                    success=False,
                    content="",
                    error="DuckDuckGo 未返回结果，可能是网络连接问题"
                )
            
            content = f"""🔍 搜索: {query} (via DuckDuckGo)
{'='*60}

📚 找到 {len(results)} 个相关结果:
"""
            for i, result in enumerate(results, 1):
                title = result.get("title", "无标题")
                url = result.get("url", "")
                snippet = result.get("snippet", "")[:300]
                
                content += f"""
{i}. {title}
   🔗 {url}
   📄 {snippet}...
"""
            
            return ToolResult(
                success=True,
                content=content,
                data={"results": results, "query": query}
            )
            
        except ImportError:
            return ToolResult(
                success=False,
                content="",
                error="未安装 duckduckgo-search。请运行: pip install duckduckgo-search"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=f"DuckDuckGo 搜索错误: {str(e)}")
    
    async def _search_mock(self, query: str, num_results: int) -> ToolResult:
        """模拟搜索（提示用户配置）"""
        content = f"""🔍 搜索: {query}
{'='*60}

⚠️ 网页搜索功能未配置

要启用搜索功能，请选择以下方案之一:

【推荐】方案 1: Tavily (高质量，带 AI 总结)
1. 访问 https://tavily.com 注册账号
2. 获取 API Key
3. 编辑 .env 文件，添加:
   TAVILY_API_KEY=tvly-your-api-key
4. 重启 ResearchFlow

方案 2: DuckDuckGo (免费，无需 API Key)
1. 运行: pip install duckduckgo-search
2. 确保 .env 中没有设置 TAVILY_API_KEY
3. 重启 ResearchFlow

方案 3: Brave Search (通过 MCP)
1. 访问 https://brave.com/search/api/ 获取 API Key
2. 配置 MCP 服务器

更多信息请查看 SEARCH_SETUP.md
"""
        return ToolResult(
            success=True,  # 返回 success=True 以便显示提示信息
            content=content,
            data={"mock": True, "query": query}
        )


class FetchURLTool(Tool):
    """获取网页内容工具"""
    
    name = "fetch_url"
    description = """获取网页内容并提取文本。

用于：
- 读取搜索结果页面的完整内容
- 获取技术文档
- 下载论文内容

注意：某些网站可能阻止爬取。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "网页 URL"
            }
        },
        "required": ["url"]
    }
    
    async def execute(self, url: str, **kwargs) -> ToolResult:
        """获取网页内容"""
        try:
            import httpx
            
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # 尝试转换为 markdown
                try:
                    from markdownify import markdownify as md
                    text = md(response.text)
                except ImportError:
                    # 降级为简单文本提取
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    text = '\n'.join(line for line in lines if line)
                
                # 限制长度
                if len(text) > 15000:
                    text = text[:15000] + "\n\n... (内容已截断，原始页面更长)"
                
                return ToolResult(
                    success=True,
                    content=f"📄 URL: {url}\n{'='*60}\n\n{text}",
                    data={"url": url, "length": len(text)}
                )
                
        except ImportError:
            return ToolResult(
                success=False,
                content="",
                error="需要安装依赖: pip install httpx beautifulsoup4 markdownify"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取网页错误: {str(e)}")


# 注册工具
register_tool(WebSearchTool())
register_tool(FetchURLTool())
