#!/usr/bin/env python3
"""
News API新闻获取器
统一参数配置，支持全局时间窗口
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

try:
    from newsapi import NewsApiClient
except ImportError:
    print("[ERROR] newsapi-python未安装，请运行: pip install newsapi-python")
    NewsApiClient = None


def fetch_newsapi_news(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从News API获取新闻
    
    Args:
        config: 配置字典，包含news_sources和time_window_hours
        
    Returns:
        新闻列表
    """
    if NewsApiClient is None:
        print("[ERROR] newsapi-python库未安装")
        return []
    
    # 获取News API配置
    news_sources = config.get('news_sources', {})
    newsapi_config = news_sources.get('newsapi', {})
    
    # 检查是否启用
    if not newsapi_config.get('enabled', False):
        print("[INFO] News API功能已禁用")
        return []
    
    # 获取API密钥（仅支持配置文件）
    api_key = newsapi_config.get('api_key')

    if not api_key:
        print(f"[ERROR] News API密钥未配置，请在配置文件的news_sources.newsapi.api_key中配置")
        return []
    
    # 获取配置参数
    category = newsapi_config.get('category', 'health')
    limit = newsapi_config.get('limit', 10)
    timeout = newsapi_config.get('timeout', 30)
    retry_count = newsapi_config.get('retry_count', 3)
    time_window_hours = config.get('time_window_hours', 24)
    
    # 计算时间范围
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=time_window_hours)
    
    # News API日期格式：YYYY-MM-DD
    start_date = start_time.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    
    print(f"[INFO] News API参数: 分类={category}, 时间范围={start_date}到{end_date}, 限制={limit}")
    
    # 执行请求（带重试机制）
    for attempt in range(retry_count):
        try:
            print(f"[INFO] News API 尝试第 {attempt + 1}/{retry_count} 次请求...")
            
            # 初始化客户端
            newsapi = NewsApiClient(api_key=api_key)
            
            # 使用get_everything方法获取新闻
            response = newsapi.get_everything(
                q=category,  # 使用分类作为关键词
                from_param=start_date,
                to=end_date,
                page_size=limit,
                sort_by='publishedAt',
                language='en'
            )
            
            # 检查响应
            if response.get('status') != 'ok':
                print(f"[ERROR] News API错误: {response.get('message', 'Unknown error')}")
                return []
            
            articles = response.get('articles', [])
            if not articles:
                print("[WARN] News API返回的数据为空")
                return []
            
            # 处理新闻数据
            news_list = []
            for article in articles:
                news_item = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('description', ''),  # 使用描述作为内容
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'source_type': 'NewsAPI'
                }
                
                # 过滤空标题和移除的文章
                if news_item['title'].strip() and '[Removed]' not in news_item['title']:
                    news_list.append(news_item)
            
            print(f"[INFO] News API成功获取 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            print(f"[WARN] News API 第 {attempt + 1} 次请求异常: {e}")
        
        # 重试前等待
        if attempt < retry_count - 1:
            print(f"[INFO] 等待2秒后重试...")
            time.sleep(2)
    
    print(f"[ERROR] News API 所有 {retry_count} 次尝试都失败")
    return []


def test_newsapi_fetcher():
    """测试News API获取器"""
    print("🧪 测试News API新闻获取器")
    print("=" * 50)
    
    # 测试配置
    test_config = {
        'time_window_hours': 24,
        'news_sources': {
            'newsapi': {
                'enabled': True,
                'api_key': 'test_key',
                'category': 'health',
                'limit': 5,
                'timeout': 30,
                'retry_count': 2
            }
        }
    }
    
    # 执行测试
    news_list = fetch_newsapi_news(test_config)
    
    print(f"获取到 {len(news_list)} 条新闻")
    for i, news in enumerate(news_list[:3], 1):
        print(f"\n新闻 {i}:")
        print(f"  标题: {news.get('title', '')[:60]}...")
        print(f"  来源: {news.get('source', '')}")
        print(f"  发布时间: {news.get('published_at', '')}")


if __name__ == "__main__":
    test_newsapi_fetcher()
