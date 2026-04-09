"""
Bash 工具 - 执行 shell 命令
"""
import asyncio
from typing import Dict, Any
from .base import Tool, ToolResult, register_tool


class BashTool(Tool):
    """Bash 工具"""
    
    name = "bash"
    description = "执行 Bash shell 命令。用于运行系统命令、查看文件、安装依赖等。"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 Bash 命令"
            },
            "timeout": {
                "type": "integer",
                "description": "命令超时时间（秒），默认 60",
                "default": 60
            },
            "working_dir": {
                "type": "string",
                "description": "工作目录（可选）",
                "default": None
            }
        },
        "required": ["command"]
    }
    
    async def execute(self, command: str, timeout: int = 60, working_dir: str = None, **kwargs) -> ToolResult:
        """执行 Bash 命令"""
        try:
            # 创建子进程
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            
            # 等待执行完成
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"命令执行超时（{timeout}秒）"
                )
            
            # 解码输出
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # 组合输出
            content = stdout_str
            if stderr_str:
                content += f"\n[stderr]:\n{stderr_str}"
            
            success = proc.returncode == 0
            
            return ToolResult(
                success=success,
                content=content.strip(),
                data={
                    "returncode": proc.returncode,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                },
                error=stderr_str if not success else None
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"执行错误: {str(e)}"
            )


# 注册工具
register_tool(BashTool())
