"""
文件操作工具
"""
import os
from pathlib import Path
from typing import Optional, List
from .base import Tool, ToolResult, register_tool


class ReadFileTool(Tool):
    """读取文件工具"""
    
    name = "read_file"
    description = "读取文件内容。支持文本文件，可指定行范围。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "offset": {
                "type": "integer",
                "description": "起始行号（从1开始）",
                "default": 1
            },
            "limit": {
                "type": "integer",
                "description": "读取行数",
                "default": 100
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, path: str, offset: int = 1, limit: int = 100, **kwargs) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"文件不存在: {path}")
            
            if not file_path.is_file():
                return ToolResult(success=False, content="", error=f"不是文件: {path}")
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start = max(0, offset - 1)
            end = min(total_lines, start + limit)
            
            selected_lines = lines[start:end]
            content = ''.join(selected_lines)
            
            # 添加行号
            numbered_content = ""
            for i, line in enumerate(selected_lines, start=start+1):
                numbered_content += f"{i:4d}: {line}"
            
            header = f"文件: {path} ({total_lines} 行，显示 {start+1}-{end})\n{'='*60}\n"
            
            return ToolResult(
                success=True,
                content=header + numbered_content,
                data={"total_lines": total_lines, "displayed": end - start}
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"读取错误: {str(e)}")


class WriteFileTool(Tool):
    """写入文件工具"""
    
    name = "write_file"
    description = "创建或覆盖文件。用于写入代码、文档等。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "content": {
                "type": "string",
                "description": "文件内容"
            },
            "append": {
                "type": "boolean",
                "description": "是否追加模式",
                "default": False
            }
        },
        "required": ["path", "content"]
    }
    
    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        try:
            file_path = Path(path)
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            action = "追加到" if append else "写入"
            return ToolResult(
                success=True,
                content=f"✅ 成功{action}文件: {path}",
                data={"path": str(file_path), "size": len(content)}
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"写入错误: {str(e)}")


class ListDirTool(Tool):
    """列出目录工具"""
    
    name = "list_dir"
    description = "列出目录内容。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "目录路径",
                "default": "."
            }
        },
        "required": []
    }
    
    async def execute(self, path: str = ".", **kwargs) -> ToolResult:
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return ToolResult(success=False, content="", error=f"目录不存在: {path}")
            
            if not dir_path.is_dir():
                return ToolResult(success=False, content="", error=f"不是目录: {path}")
            
            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "📁" if item.is_dir() else "📄"
                size = ""
                if item.is_file():
                    try:
                        size_bytes = item.stat().st_size
                        if size_bytes < 1024:
                            size = f"{size_bytes}B"
                        elif size_bytes < 1024 * 1024:
                            size = f"{size_bytes/1024:.1f}KB"
                        else:
                            size = f"{size_bytes/(1024*1024):.1f}MB"
                    except:
                        pass
                items.append(f"{item_type} {item.name:<40} {size:>10}")
            
            header = f"目录: {path}\n{'='*60}\n"
            content = header + '\n'.join(items)
            
            return ToolResult(
                success=True,
                content=content,
                data={"count": len(items)}
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"列出目录错误: {str(e)}")


class GrepTool(Tool):
    """搜索文件工具"""
    
    name = "grep"
    description = "在文件中搜索内容（类似 grep 命令）。"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "搜索模式"
            },
            "path": {
                "type": "string",
                "description": "搜索路径",
                "default": "."
            },
            "glob": {
                "type": "string",
                "description": "文件匹配模式，如 '*.py'",
                "default": "*"
            }
        },
        "required": ["pattern"]
    }
    
    async def execute(self, pattern: str, path: str = ".", glob: str = "*", **kwargs) -> ToolResult:
        try:
            import re
            
            search_path = Path(path)
            matches = []
            
            # 递归搜索
            for file_path in search_path.rglob(glob):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            for i, line in enumerate(f, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matches.append(f"{file_path}:{i}: {line.strip()}")
                                    if len(matches) >= 50:  # 限制结果数
                                        break
                    except:
                        pass
                
                if len(matches) >= 50:
                    break
            
            if matches:
                content = f"找到 {len(matches)} 个匹配:\n{'='*60}\n" + '\n'.join(matches[:50])
            else:
                content = "未找到匹配"
            
            return ToolResult(success=True, content=content, data={"matches": len(matches)})
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"搜索错误: {str(e)}")


# 注册工具
register_tool(ReadFileTool())
register_tool(WriteFileTool())
register_tool(ListDirTool())
register_tool(GrepTool())
