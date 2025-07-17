import feedparser
import requests
import yaml
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import re
from urllib.parse import urljoin, urlparse
# 删除了rss_url_generator模块，直接使用原始URL

def load_rss_feeds(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从独立文件加载RSS源配置
    """
    # 检查是否有RSS文件配置
    rss_feeds_file = config.get('rss_feeds_file', 'rss_feeds.yaml')

    # 如果配置中直接有rss_feeds，优先使用
    if 'rss_feeds' in config and config['rss_feeds']:
        return config['rss_feeds']

    # 尝试从独立文件加载
    if os.path.exists(rss_feeds_file):
        try:
            with open(rss_feeds_file, 'r', encoding='utf-8') as f:
                rss_config = yaml.safe_load(f)
                rss_feeds = rss_config.get('rss_feeds', [])

                # 转换简化的URL列表为标准格式
                standardized_feeds = []
                for i, feed in enumerate(rss_feeds):
                    if isinstance(feed, str):
                        # 简化格式：直接是URL字符串
                        standardized_feeds.append({
                            'name': f'RSS源{i+1}',
                            'url': feed
                        })
                    elif isinstance(feed, dict):
                        # 标准格式：包含name和url的字典
                        standardized_feeds.append(feed)

                print(f"[INFO] 成功加载 {len(standardized_feeds)} 个RSS源")
                return standardized_feeds

        except Exception as e:
            print(f"[ERROR] 加载RSS配置文件失败: {e}")
            return []
    else:
        print(f"[WARN] RSS配置文件不存在: {rss_feeds_file}")
        return []

def fetch_rss_news(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从RSS源获取新闻（RSS是必须启动的）
    """
    rss_settings = config.get('rss_settings', {})

    rss_feeds = load_rss_feeds(config)
    if not rss_feeds:
        print("[WARN] 未配置RSS源")
        return []

    time_window = config.get('time_window_hours', 24)  # 使用统一的时间窗口参数
    max_articles_per_feed = rss_settings.get('max_articles_per_feed', 10)  # 每个RSS源的文章数限制

    # RSS源直接使用配置文件中的URL（已包含时间参数）
    time_desc = f"最近{time_window}小时"

    # 计算时间范围
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=time_window)

    print(f"[INFO] 开始获取RSS新闻，时间范围: {cutoff_time} 到 {now} (UTC)")
    print(f"[INFO] 共 {len(rss_feeds)} 个RSS源，时间窗口: {time_desc}")
    print(f"[INFO] 每个RSS源限制: {max_articles_per_feed} 条，无总数限制")

    all_news = []
    
    # 按优先级排序RSS源
    sorted_feeds = sorted(rss_feeds, key=lambda x: x.get('priority', 5))
    
    for feed_config in sorted_feeds:
        feed_name = feed_config.get('name', 'Unknown')
        feed_url = feed_config.get('url', '')
        priority = feed_config.get('priority', 5)

        if not feed_url:
            print(f"[WARN] RSS源 {feed_name} 缺少URL")
            continue

        print(f"[INFO] 获取RSS源: {feed_name} (优先级: {priority}) - 当前已获取: {len(all_news)} 条")
        
        # 从配置读取RSS参数
        rss_settings = config.get('rss_settings', {})
        user_agent = rss_settings.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        timeout = rss_settings.get('timeout', 45)
        max_retries = rss_settings.get('retry_count', 3)

        # 添加重试机制和浏览器伪装
        for attempt in range(max_retries):
            try:
                print(f"[INFO] RSS源 {feed_name} 尝试第 {attempt + 1}/{max_retries} 次获取...")

                # 设置完整的浏览器伪装头部
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }

                # 礼貌的访问：增加超时时间，添加会话保持
                session = requests.Session()
                session.headers.update(headers)

                # 获取RSS内容，使用配置的超时时间
                response = session.get(feed_url, timeout=timeout, allow_redirects=True)
                response.raise_for_status()

                # 成功获取，跳出重试循环
                break

            except requests.exceptions.Timeout:
                print(f"[WARN] RSS源 {feed_name} 第 {attempt + 1} 次尝试超时")
                if attempt < max_retries - 1:
                    # 超时后等待更长时间
                    wait_time = 5 + (attempt * 2)  # 递增等待时间
                    print(f"[INFO] 等待{wait_time}秒后重试...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[ERROR] RSS源 {feed_name} 所有 {max_retries} 次尝试都超时")
                    continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"[WARN] RSS源 {feed_name} 第 {attempt + 1} 次尝试被限流 (429)")
                    if attempt < max_retries - 1:
                        # 被限流后等待更长时间
                        wait_time = 10 + (attempt * 5)  # 更长的等待时间
                        print(f"[INFO] 被限流，等待{wait_time}秒后重试...")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ERROR] RSS源 {feed_name} 持续被限流，跳过")
                        continue
                elif e.response.status_code == 403:
                    print(f"[WARN] RSS源 {feed_name} 第 {attempt + 1} 次尝试被禁止访问 (403)")
                    if attempt < max_retries - 1:
                        # 403错误后等待并尝试不同的User-Agent
                        wait_time = 3 + attempt
                        print(f"[INFO] 访问被禁止，等待{wait_time}秒后重试...")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ERROR] RSS源 {feed_name} 持续被禁止访问，跳过")
                        continue
                else:
                    print(f"[WARN] RSS源 {feed_name} 第 {attempt + 1} 次尝试HTTP错误: {e}")
                    if attempt < max_retries - 1:
                        print(f"[INFO] 等待3秒后重试...")
                        import time
                        time.sleep(3)
                        continue
                    else:
                        print(f"[ERROR] RSS源 {feed_name} 所有 {max_retries} 次尝试都失败")
                        continue

            except Exception as e:
                print(f"[WARN] RSS源 {feed_name} 第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"[INFO] 等待3秒后重试...")
                    import time
                    time.sleep(3)
                    continue
                else:
                    print(f"[ERROR] RSS源 {feed_name} 所有 {max_retries} 次尝试都失败")
                    continue

        # 如果所有重试都失败，跳到下一个RSS源
        if 'response' not in locals():
            continue

        # 在成功获取后，礼貌地等待一下再处理下一个RSS源
        import time
        time.sleep(2)

        try:
            
            # 解析RSS
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"[WARN] RSS源 {feed_name} 解析可能有问题: {feed.bozo_exception}")
            
            feed_news_count = 0
            
            # 使用已读取的文章数量限制
            for entry in feed.entries[:max_articles_per_feed]:
                # 解析发布时间
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # 检查时间范围 - 只处理24小时内的新闻
                if published_time:
                    if published_time < cutoff_time:
                        continue
                else:
                    # 没有发布时间的新闻跳过
                    print(f"[WARN] 新闻 '{title[:50]}...' 没有发布时间，跳过")
                    continue
                
                # 提取新闻信息
                title = entry.get('title', '').strip()
                description = entry.get('description', '').strip()
                link = entry.get('link', '').strip()

                # 尝试获取更完整的内容
                content = ''

                # 优先级：content > summary > description
                if hasattr(entry, 'content') and entry.content:
                    # 有些RSS有content字段
                    if isinstance(entry.content, list) and len(entry.content) > 0:
                        content = entry.content[0].get('value', '')
                    else:
                        content = str(entry.content)
                elif hasattr(entry, 'summary') and entry.summary:
                    # 使用summary字段
                    content = entry.summary
                elif description:
                    # 最后使用description
                    content = description

                # 清理HTML标签
                if content:
                    content = re.sub(r'<[^>]+>', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()

                if description:
                    description = re.sub(r'<[^>]+>', '', description)
                    description = re.sub(r'\s+', ' ', description).strip()

                if not title or not link:
                    continue

                # RSS内容通常都比较短，需要AI补全
                needs_enhancement = len(content) < 500  # 少于500字符需要AI补全

                news_item = {
                    'title': title,
                    'description': description,
                    'url': link,
                    'published_at': published_time.isoformat() if published_time else now.isoformat(),
                    'source': feed_name,
                    'content': content,
                    'rss_priority': priority,
                    'needs_full_content': needs_enhancement  # 标记是否需要AI补全
                }
                
                all_news.append(news_item)
                feed_news_count += 1
            
            print(f"[INFO] RSS源 {feed_name} 获取到 {feed_news_count} 条新闻")
            
        except Exception as e:
            print(f"[ERROR] 获取RSS源 {feed_name} 失败: {str(e)}")
            continue
    
    # 按发布时间排序（最新的在前）
    all_news.sort(key=lambda x: x['published_at'], reverse=True)
    
    print(f"[INFO] RSS获取完成，共获得 {len(all_news)} 条新闻")
    
    return all_news

def enhance_rss_news_with_full_content(news_list: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    为RSS新闻获取完整内容
    """
    if not news_list:
        return news_list
    
    print(f"[INFO] 开始为 {len(news_list)} 条RSS新闻获取完整内容...")
    
    # 导入内容获取器
    try:
        from .content_fetcher import fetch_full_content
    except ImportError:
        print("[ERROR] 无法导入内容获取器")
        return news_list
    
    enhanced_news = []
    
    for i, news_item in enumerate(news_list, 1):
        print(f"[INFO] 获取第 {i}/{len(news_list)} 条RSS新闻全文: {news_item['title'][:50]}...")
        
        # 尝试获取完整内容
        full_content = fetch_full_content(news_item['url'], config)
        
        if full_content and len(full_content.strip()) > len(news_item.get('content', '')):
            # 成功获取到更完整的内容
            news_item['content'] = full_content
            print(f"[INFO] 成功获取完整内容，长度: {len(full_content)} 字符")
        else:
            # 使用原始描述
            print(f"[WARN] 未能获取完整内容，使用原始描述")
        
        enhanced_news.append(news_item)
    
    print(f"[INFO] RSS新闻内容增强完成")
    return enhanced_news
