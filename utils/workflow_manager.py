#!/usr/bin/env python3
"""
工作流程管理器 - 统一管理整个新闻处理流程
"""

from datetime import datetime
from typing import Dict, Any, List
import time

from .news_processor import NewsProcessor
from .news_publisher import NewsPublisher
from .ai_analyzer import AIContentAnalyzer
from .rss_fetcher import fetch_rss_news


class WorkflowManager:
    """新闻处理工作流程管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化工作流程管理器"""
        self.config = config
        self.news_processor = NewsProcessor(config)
        self.news_publisher = NewsPublisher(config)
        
    def execute_daily_task(self) -> Dict[str, Any]:
        """执行每日新闻处理任务"""
        print(f"\n[INFO] 开始执行任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (本地时间)")
        
        try:
            # 步骤1: 收集新闻
            print("\n[INFO] ========== 步骤1: 收集新闻 ==========")
            all_news = self._collect_all_news()
            
            if not all_news:
                print("[WARN] 没有收集到任何新闻")
                return self._create_result(0, 0, 0, "没有收集到新闻")
            
            print(f"[INFO] 总共收集到 {len(all_news)} 条新闻")
            
            # 步骤2: 处理新闻
            print("\n[INFO] ========== 步骤2: 处理新闻 ==========")
            processed_news = self.news_processor.process_news_batch(all_news)
            
            if not processed_news:
                print("[WARN] 没有新闻通过处理流程")
                return self._create_result(len(all_news), 0, 0, "没有新闻通过处理")
            
            print(f"[INFO] 共 {len(processed_news)} 条新闻完成处理")
            
            # 步骤3: 发布新闻
            print("\n[INFO] ========== 步骤3: 发布新闻 ==========")
            publish_result = self.news_publisher.publish_news_batch(processed_news)
            
            # 返回执行结果
            return self._create_result(
                len(all_news),
                len(processed_news), 
                publish_result['sent_count'],
                "任务执行完成",
                publish_result
            )
            
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return self._create_result(0, 0, 0, error_msg)

    def _collect_all_news(self) -> List[Dict[str, Any]]:
        """收集所有新闻源的新闻"""
        all_news = []

        # 第一步：从RSS获取新闻
        print("[INFO] 第一步：从RSS获取新闻...")
        try:
            rss_news = fetch_rss_news(self.config)
            if rss_news:
                all_news.extend(rss_news)
                print(f"[INFO] RSS获取到 {len(rss_news)} 条新闻")
            else:
                print("[WARN] RSS未获取到任何新闻")
        except Exception as e:
            print(f"[ERROR] RSS获取失败: {e}")

        # 第二步：从MediaStack获取新闻
        print("[INFO] 第二步：从MediaStack获取新闻...")
        try:
            from utils.mediastack_fetcher import fetch_mediastack_news
            mediastack_news = fetch_mediastack_news(self.config)
            if mediastack_news:
                print(f"[INFO] MediaStack获取到 {len(mediastack_news)} 条新闻")
                all_news.extend(mediastack_news)
            else:
                print("[WARN] MediaStack未获取到任何新闻")
        except Exception as e:
            print(f"[ERROR] MediaStack获取失败: {e}")

        # 第三步：从News API获取新闻
        print("[INFO] 第三步：从News API获取新闻...")
        try:
            from utils.newsapi_fetcher import fetch_newsapi_news
            newsapi_news = fetch_newsapi_news(self.config)
            if newsapi_news:
                print(f"[INFO] News API获取到 {len(newsapi_news)} 条新闻")
                all_news.extend(newsapi_news)
            else:
                print("[WARN] News API未获取到任何新闻")
        except Exception as e:
            print(f"[ERROR] News API获取失败: {e}")



        print(f"[INFO] 新闻收集完成，总计 {len(all_news)} 条新闻")
        return all_news

    def _create_result(self, collected: int, processed: int, sent: int,
                      message: str, details: Dict = None) -> Dict[str, Any]:
        """创建执行结果"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'collected_count': collected,
            'processed_count': processed,
            'sent_count': sent,
            'message': message,
            'success': sent > 0
        }
        
        if details:
            result.update(details)
            
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'timestamp': datetime.now().isoformat(),
            'config_loaded': bool(self.config),
            'news_sources': {
                'rss_enabled': bool(self.config.get('rss_feeds')),
                'mediastack_enabled': self.config.get('news_sources', {}).get('mediastack', {}).get('enabled', False),
                'newsapi_enabled': self.config.get('news_sources', {}).get('newsapi', {}).get('enabled', False)
            },
            'ai_services': {
                'gemini_enabled': bool(self.config.get('gemini_api_keys')),
                'openrouter_enabled': bool(self.config.get('openrouter_api_keys'))
            },
            'content_service': {
                'firecrawl_enabled': bool(self.config.get('firecrawl_api_key'))
            },
            'webhook_enabled': bool(self.config.get('webhook_url')),
            'max_send_limit': self.config.get('max_send_limit', 3),
            'min_relevance_score': self.config.get('ai_settings', {}).get('min_relevance_score', 6)
        }


if __name__ == "__main__":
    # 测试代码
    from .config_manager import ConfigManager
    
    print("🧪 测试工作流程管理器...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        workflow = WorkflowManager(config)
        
        # 获取状态
        status = workflow.get_status()
        print("📊 系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 工作流程管理器初始化成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
