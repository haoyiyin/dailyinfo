#!/usr/bin/env python3
"""
新闻发布器 - 统一管理新闻的排序、限制和推送发布
"""

from typing import Dict, Any, List
import time
from .feishu import push_to_webhook


class NewsPublisher:
    """新闻发布器 - 负责新闻的排序、限制和推送发布"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化新闻发布器"""
        self.config = config
        self.max_send_limit = config.get('max_send_limit', 3)
        
    def publish_news_batch(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量发布新闻"""
        if not news_list:
            print("[WARN] 没有新闻需要发布")
            return self._create_publish_result(0, 0, [])
        
        print(f"[INFO] 开始批量发布 {len(news_list)} 条新闻")
        
        # 步骤1: 按AI评分排序
        sorted_news = self.sort_news_by_score(news_list)
        
        # 步骤2: 限制发布数量
        selected_news = self.limit_news_count(sorted_news)
        
        # 步骤3: 执行推送
        publish_result = self.push_news_to_webhook(selected_news)
        
        return publish_result
    
    def sort_news_by_score(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按AI评分排序新闻"""
        print("[INFO] 按AI评分排序新闻...")
        
        # 按AI评分降序排序
        sorted_news = sorted(news_list, key=lambda x: x.get('ai_score', 0.0), reverse=True)
        
        print("[INFO] 排序结果:")
        for i, news in enumerate(sorted_news, 1):
            title = news.get('title', '')[:50]
            score = news.get('ai_score', 0.0)
            print(f"  {i}. {title}... (评分: {score:.2f})")
        
        return sorted_news
    
    def limit_news_count(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """限制新闻发布数量"""
        print(f"[INFO] 限制发布数量 (最大: {self.max_send_limit}条)")
        
        if len(news_list) <= self.max_send_limit:
            print(f"[INFO] 共 {len(news_list)} 条新闻，全部发布")
            return news_list
        
        # 选择前N条高分新闻
        selected_news = news_list[:self.max_send_limit]
        
        print(f"[INFO] 通过评估的新闻有 {len(news_list)} 条，按评分选择前 {self.max_send_limit} 条发布")
        
        print("[INFO] 选中发布的新闻:")
        for i, news in enumerate(selected_news, 1):
            title = news.get('title', '')[:50]
            score = news.get('ai_score', 0.0)
            print(f"  ✅ {i}. {title}... (评分: {score:.2f})")
        
        print("[INFO] 未选中的新闻:")
        for i, news in enumerate(news_list[self.max_send_limit:], self.max_send_limit + 1):
            title = news.get('title', '')[:50]
            score = news.get('ai_score', 0.0)
            print(f"  ❌ {i}. {title}... (评分: {score:.2f}) - 未发布")
        
        return selected_news
    
    def push_news_to_webhook(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """推送新闻到webhook"""
        print(f"[INFO] 开始推送 {len(news_list)} 条新闻到webhook...")
        
        sent_count = 0
        failed_count = 0
        sent_news = []
        failed_news = []
        
        for i, news in enumerate(news_list, 1):
            try:
                title = news.get('title', '')[:50]
                score = news.get('ai_score', 0.0)
                print(f"[INFO] 推送第 {i}/{len(news_list)} 条新闻 (评分: {score:.2f}): {title}...")
                
                # 移除ai_score字段，避免推送到webhook
                webhook_data = {k: v for k, v in news.items() if k != 'ai_score'}
                
                if push_to_webhook(webhook_data, self.config):
                    sent_count += 1
                    sent_news.append(news)
                    print(f"[INFO] 第 {i} 条新闻推送成功")
                else:
                    failed_count += 1
                    failed_news.append(news)
                    print(f"[ERROR] 第 {i} 条新闻推送失败")
                
                # 添加间隔，避免API限制
                if i < len(news_list):
                    time.sleep(2)
                    
            except Exception as e:
                failed_count += 1
                failed_news.append(news)
                print(f"[ERROR] 推送新闻时出错: {str(e)}")
                continue
        
        result = self._create_publish_result(sent_count, failed_count, sent_news, failed_news)
        
        print(f"[INFO] 推送完成 - 成功: {sent_count}, 失败: {failed_count}")
        return result
    
    def _create_publish_result(self, sent_count: int, failed_count: int, 
                              sent_news: List[Dict] = None, 
                              failed_news: List[Dict] = None) -> Dict[str, Any]:
        """创建发布结果"""
        return {
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_processed': sent_count + failed_count,
            'success_rate': sent_count / (sent_count + failed_count) * 100 if (sent_count + failed_count) > 0 else 0,
            'sent_news': sent_news or [],
            'failed_news': failed_news or [],
            'max_send_limit': self.max_send_limit
        }
    
    def get_publisher_stats(self) -> Dict[str, Any]:
        """获取发布器统计信息"""
        return {
            'webhook_enabled': bool(self.config.get('webhook_url')),
            'webhook_configured': self.config.get('webhook_url') != "YOUR_WEBHOOK_URL_HERE",
            'max_send_limit': self.max_send_limit,
            'push_time': self.config.get('push_time'),
            'timezone': self.config.get('timezone')
        }
    
    def test_webhook_connection(self) -> bool:
        """测试webhook连接"""
        test_data = {
            "message_type": "text",
            "title": "测试连接",
            "content": "这是一条测试消息，用于验证webhook连接是否正常。",
            "original_link": "https://example.com/test"
        }
        
        try:
            print("[INFO] 测试webhook连接...")
            result = push_to_webhook(test_data, self.config)
            
            if result:
                print("[INFO] ✅ Webhook连接测试成功")
                return True
            else:
                print("[ERROR] ❌ Webhook连接测试失败")
                return False
                
        except Exception as e:
            print(f"[ERROR] Webhook连接测试异常: {str(e)}")
            return False


if __name__ == "__main__":
    # 测试代码
    from .config_manager import ConfigManager
    
    print("🧪 测试新闻发布器...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        publisher = NewsPublisher(config)
        
        # 获取统计信息
        stats = publisher.get_publisher_stats()
        print("📊 发布器统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 新闻发布器初始化成功")
        
        # 可选：测试webhook连接（注释掉避免实际推送）
        # print("\n🔗 测试webhook连接...")
        # publisher.test_webhook_connection()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
