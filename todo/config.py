"""
Configuration management for Todo CLI.

Handles persistent storage and retrieval of application settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import typer


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.app_dir = Path(typer.get_app_dir("todo-cli"))
        self.config_file = self.app_dir / "config.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.app_dir, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise typer.Exit(f"Failed to save config: {e}")
    
    def get_chat_config(self) -> Dict[str, Any]:
        """获取聊天配置"""
        config = self._load_config()
        return config.get('chat', {})
    
    def set_chat_config(self, **kwargs):
        """设置聊天配置"""
        config = self._load_config()
        if 'chat' not in config:
            config['chat'] = {}
        
        # 更新配置项
        for key, value in kwargs.items():
            if value is not None:
                config['chat'][key] = value
        
        self._save_config(config)
    
    def get_chat_setting(self, key: str, default: Any = None) -> Any:
        """获取单个聊天配置项"""
        chat_config = self.get_chat_config()
        return chat_config.get(key, default)
    
    def reset_chat_config(self):
        """重置聊天配置"""
        config = self._load_config()
        if 'chat' in config:
            del config['chat']
        self._save_config(config)
    
    def has_chat_config(self) -> bool:
        """检查是否有聊天配置"""
        chat_config = self.get_chat_config()
        return bool(chat_config.get('api_key'))
    
    def get_effective_chat_config(self, 
                                  api_key: Optional[str] = None,
                                  base_url: Optional[str] = None,
                                  model: Optional[str] = None) -> Dict[str, Any]:
        """获取有效的聊天配置（命令行参数 > 配置文件 > 默认值）"""
        saved_config = self.get_chat_config()
        
        # 配置优先级：命令行参数 > 配置文件 > 默认值
        effective_config = {
            'api_key': api_key or saved_config.get('api_key'),
            'base_url': base_url or saved_config.get('base_url'),
            'model': model or saved_config.get('model', 'gpt-3.5-turbo')
        }
        
        return effective_config


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager
