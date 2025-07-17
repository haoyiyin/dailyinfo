#!/usr/bin/env python3
"""
MediaStack新闻获取器
统一参数配置，支持全局时间窗口
"""

import requests
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional


def fetch_mediastack_news(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从MediaStack获取新闻
    
    Args:
        config: 配置字典，包含news_sources和time_window_hours
        
    Returns:
        新闻列表
    """
    # 获取MediaStack配置
    news_sources = config.get('news_sources', {})
    mediastack_config = news_sources.get('mediastack', {})
    
    # 检查是否启用
    if not mediastack_config.get('enabled', False):
        print("[INFO] MediaStack功能已禁用")
        return []
    
    # 获取API密钥（仅支持配置文件）
    api_key = mediastack_config.get('api_key')

    if not api_key:
        print(f"[ERROR] MediaStack API密钥未配置，请在配置文件的news_sources.mediastack.api_key中配置")
        return []
    
    # 获取配置参数
    category = mediastack_config.get('category', 'health')
    limit = mediastack_config.get('limit', 10)
    timeout = mediastack_config.get('timeout', 30)
    retry_count = mediastack_config.get('retry_count', 3)
    time_window_hours = config.get('time_window_hours', 24)
    
    # 计算时间范围
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=time_window_hours)
    
    # MediaStack日期格式：YYYY-MM-DD,YYYY-MM-DD
    start_date = start_time.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    date_range = f"{start_date},{end_date}"
    
    # 构建请求参数
    params = {
        'access_key': api_key,
        'categories': category,
        'date': date_range,
        'limit': limit,
        'sort': 'published_desc'
    }
    
    print(f"[INFO] MediaStack参数: 分类={category}, 时间范围={date_range}, 限制={limit}")
    
    # 执行请求（带重试机制）
    for attempt in range(retry_count):
        try:
            print(f"[INFO] MediaStack API 尝试第 {attempt + 1}/{retry_count} 次请求...")
            
            response = requests.get(
                'http://api.mediastack.com/v1/news',
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API响应
            if 'error' in data:
                print(f"[ERROR] MediaStack API错误: {data['error']}")
                return []
            
            if not data.get('data'):
                print("[WARN] MediaStack API返回的数据为空")
                return []
            
            # 处理新闻数据
            news_list = []
            for item in data['data']:
                news_item = {
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'content': item.get('description', ''),  # 使用描述作为内容
                    'url': item.get('url', ''),
                    'published_at': item.get('published_at', ''),
                    'source': item.get('source', ''),
                    'source_type': 'MediaStack'
                }
                
                # 过滤空标题
                if news_item['title'].strip():
                    news_list.append(news_item)
            
            print(f"[INFO] MediaStack成功获取 {len(news_list)} 条新闻")
            return news_list
            
        except requests.exceptions.Timeout:
            print(f"[WARN] MediaStack API 第 {attempt + 1} 次请求超时")
        except requests.exceptions.ConnectionError:
            print(f"[WARN] MediaStack API 第 {attempt + 1} 次连接失败")
        except requests.exceptions.HTTPError as e:
            print(f"[WARN] MediaStack API 第 {attempt + 1} 次HTTP错误: {e}")
        except Exception as e:
            print(f"[WARN] MediaStack API 第 {attempt + 1} 次请求异常: {e}")
        
        # 重试前等待
        if attempt < retry_count - 1:
            print(f"[INFO] 等待2秒后重试...")
            time.sleep(2)
    
    print(f"[ERROR] MediaStack API 所有 {retry_count} 次尝试都失败")
    return []


def test_mediastack_fetcher():
    """测试MediaStack获取器"""
    print("🧪 测试MediaStack新闻获取器")
    print("=" * 50)
    
    # 测试配置
    test_config = {
        'time_window_hours': 24,
        'news_sources': {
            'mediastack': {
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
    news_list = fetch_mediastack_news(test_config)
    
    print(f"获取到 {len(news_list)} 条新闻")
    for i, news in enumerate(news_list[:3], 1):
        print(f"\n新闻 {i}:")
        print(f"  标题: {news.get('title', '')[:60]}...")
        print(f"  来源: {news.get('source', '')}")
        print(f"  发布时间: {news.get('published_at', '')}")


if __name__ == "__main__":
    test_mediastack_fetcher()
