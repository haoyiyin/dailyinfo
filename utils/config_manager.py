#!/usr/bin/env python3
"""
配置管理器 - 统一管理配置文件加载和环境变量
"""

import yaml
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器"""
        if config_path is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(script_dir, 'config.yaml')
        
        self.config_path = config_path
        self.config = None
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件，支持环境变量覆盖"""
        try:
            # 加载YAML配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 使用环境变量覆盖敏感配置
            self._apply_environment_overrides()
            
            # 验证配置
            self._validate_config()
            
            print("[DEBUG] 加载配置:", {k: ('***' if 'key' in k or 'url' in k else v) for k, v in self.config.items()})
            return self.config
            
        except Exception as e:
            print(f"[ERROR] 加载配置文件失败: {str(e)}")
            raise
    
    def _apply_environment_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            'gemini_api_keys': 'GEMINI_API_KEYS',
            'openrouter_api_keys': 'OPENROUTER_API_KEYS',
            'firecrawl_api_key': 'FIRECRAWL_API_KEY',
            'webhook_url': 'WEBHOOK_URL'
        }
        
        for config_key, env_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                self.config[config_key] = env_value
                print(f"[INFO] 使用环境变量 {env_key} 覆盖配置")
    
    def _validate_config(self):
        """验证配置完整性"""
        required_keys = [
            'daily_run_time', 'timezone', 'max_send_limit'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in self.config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"配置文件缺少必需的键: {missing_keys}")
        
        # 验证AI设置
        if 'ai_settings' not in self.config:
            raise ValueError("配置文件缺少ai_settings部分")
        
        ai_settings = self.config['ai_settings']
        if 'min_relevance_score' not in ai_settings:
            raise ValueError("ai_settings缺少min_relevance_score")
        
        # 验证新闻源设置
        news_sources_config = self.config.get('news_sources', {})
        news_sources = [
            self.config.get('rss_feeds'),
            news_sources_config.get('mediastack', {}).get('api_key'),
            news_sources_config.get('newsapi', {}).get('api_key')
        ]
        
        if not any(news_sources):
            print("[WARN] 没有配置任何新闻源")
    
    def get_news_source_config(self) -> Dict[str, Any]:
        """获取新闻源配置"""
        return {
            'rss_feeds': self.config.get('rss_feeds', []),
            'rss_settings': self.config.get('rss_settings', {}),
            'news_sources': self.config.get('news_sources', {})
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return {
            'gemini_api_keys': self.config.get('gemini_api_keys', []),
            'gemini_model': self.config.get('gemini_model'),
            'openrouter_api_keys': self.config.get('openrouter_api_keys', []),
            'openrouter_model': self.config.get('openrouter_model'),
            'ai_settings': self.config.get('ai_settings', {}),
            'firecrawl_api_key': self.config.get('firecrawl_api_key')
        }
    
    def get_publisher_config(self) -> Dict[str, Any]:
        """获取发布配置"""
        return {
            'webhook_url': self.config.get('webhook_url'),
            'max_send_limit': self.config.get('max_send_limit', 10),
            'daily_run_time': self.config.get('daily_run_time', '06:00'),
            'timezone': self.config.get('timezone', 'Asia/Shanghai')
        }
    
    def get_full_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        if self.config is None:
            raise ValueError("配置尚未加载，请先调用load_config()")
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        if self.config is None:
            raise ValueError("配置尚未加载，请先调用load_config()")
        
        self.config.update(updates)
        print(f"[INFO] 配置已更新: {list(updates.keys())}")
    
    def save_config(self, backup: bool = True):
        """保存配置到文件"""
        if self.config is None:
            raise ValueError("没有配置可保存")
        
        try:
            # 创建备份
            if backup and os.path.exists(self.config_path):
                backup_path = f"{self.config_path}.backup"
                import shutil
                shutil.copy2(self.config_path, backup_path)
                print(f"[INFO] 配置备份已创建: {backup_path}")
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            print(f"[INFO] 配置已保存到: {self.config_path}")
            
        except Exception as e:
            print(f"[ERROR] 保存配置失败: {str(e)}")
            raise


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试配置管理器...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print("✅ 配置加载成功")
        print(f"📊 配置项数量: {len(config)}")
        
        # 测试分类配置获取
        news_config = config_manager.get_news_source_config()
        ai_config = config_manager.get_ai_config()
        publisher_config = config_manager.get_publisher_config()
        
        print(f"📰 新闻源配置: {len(news_config)} 项")
        print(f"🤖 AI配置: {len(ai_config)} 项")
        print(f"📤 发布配置: {len(publisher_config)} 项")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
