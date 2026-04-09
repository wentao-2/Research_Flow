"""
ResearchFlow 配置管理
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ResearchFlowConfig:
    """ResearchFlow 配置"""
    
    # API 配置
    api_key: str = ""
    base_url: str = "https://api.kimi.com/coding/"
    
    # 模型配置
    model: str = "kimi-k2.5"
    provider: str = "anthropic"
    
    # 路径配置
    project_dir: Path = field(default_factory=lambda: Path("/ext/ResearchFlow"))
    workspace_dir: Path = field(default_factory=lambda: Path("/ext/ResearchFlow/workspace"))
    memory_dir: Path = field(default_factory=lambda: Path("/ext/ResearchFlow/memory"))
    skills_dir: Path = field(default_factory=lambda: Path("/ext/.claude/skills"))
    
    # 功能开关
    enable_web_search: bool = True
    enable_skills: bool = True
    enable_memory: bool = True
    auto_approve: bool = False
    
    # 工作流配置
    max_iterations: int = 100
    recursion_limit: int = 1000
    
    @classmethod
    def from_env(cls) -> "ResearchFlowConfig":
        """从环境变量加载配置"""
        config = cls()
        
        # 加载 .env 文件
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)
        
        # API 配置
        config.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        config.base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.kimi.com/coding/")
        
        # 模型配置
        config.model = os.environ.get("DEFAULT_MODEL", "kimi-k2.5")
        config.provider = os.environ.get("DEFAULT_PROVIDER", "anthropic")
        
        # 功能开关
        config.enable_web_search = os.environ.get("ENABLE_WEB_SEARCH", "true").lower() == "true"
        config.auto_approve = os.environ.get("WORKFLOW_AUTO_APPROVE", "false").lower() == "true"
        
        # 数值配置
        config.max_iterations = int(os.environ.get("MAX_ITERATIONS", "100"))
        
        # 确保目录存在
        config.workspace_dir.mkdir(parents=True, exist_ok=True)
        config.memory_dir.mkdir(parents=True, exist_ok=True)
        
        return config
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.api_key:
            print("❌ 错误: ANTHROPIC_API_KEY 未设置")
            print("   请在 .env 文件中设置 API Key")
            return False
        return True


# 全局配置实例
_config: Optional[ResearchFlowConfig] = None


def get_config() -> ResearchFlowConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = ResearchFlowConfig.from_env()
    return _config
