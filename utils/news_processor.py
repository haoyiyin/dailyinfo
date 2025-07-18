#!/usr/bin/env python3
"""
新闻处理器 - 统一管理新闻的AI评估、内容获取和优化处理
"""

from typing import Dict, Any, List
from .ai_analyzer import AIContentAnalyzer
from .news_deduplicator import NewsDeduplicator
from .zyte_client import create_zyte_client

def fetch_full_content_with_fallback(url: str, api_config: Dict[str, Any]) -> str:
    """
    使用FireCrawl + Zyte备用机制获取完整内容

    流程：
    1. 首先尝试FireCrawl
    2. FireCrawl失败时使用Zyte (最多重试3次)
    3. 都失败时返回空字符串
    """

    # 第一步：尝试FireCrawl（重试3次）
    print(f"[INFO] 尝试使用FireCrawl抓取: {url}")
    firecrawl_content = _try_firecrawl(url, api_config, max_retries=3)

    if firecrawl_content:
        print(f"[INFO] FireCrawl抓取成功，内容长度: {len(firecrawl_content)} 字符")
        return firecrawl_content

    # 第二步：FireCrawl失败，尝试Zyte
    print(f"[WARN] FireCrawl抓取失败，尝试使用Zyte备用抓取...")
    zyte_content = _try_zyte(url, api_config, max_retries=3)

    if zyte_content:
        print(f"[INFO] Zyte备用抓取成功，内容长度: {len(zyte_content)} 字符")
        return zyte_content

    # 第三步：都失败了
    print(f"[ERROR] FireCrawl和Zyte都抓取失败: {url}")
    return ""


def _try_firecrawl(url: str, api_config: Dict[str, Any], max_retries: int = 3) -> str:
    """尝试使用FireCrawl抓取内容，支持重试"""
    try:
        from firecrawl import FirecrawlApp

        api_key = api_config.get('firecrawl_api_key', '')
        if not api_key or api_key.startswith('YOUR_'):
            print("[WARN] FireCrawl API密钥未配置")
            return ""

        app = FirecrawlApp(api_key=api_key)

        for attempt in range(max_retries):
            try:
                print(f"[INFO] FireCrawl尝试第 {attempt + 1}/{max_retries} 次...")

                # 尝试使用scrape模式（根据新的API格式）
                try:
                    # 使用新的API格式：app.scrape_url(url, formats=['markdown', 'html'])
                    result = app.scrape_url(url, formats=['markdown', 'html'])

                    if result:
                        # 优先使用markdown格式
                        if hasattr(result, 'markdown') and result.markdown:
                            print(f"[INFO] FireCrawl scrape模式（markdown）成功")
                            return result.markdown
                        elif hasattr(result, 'html') and result.html:
                            print(f"[INFO] FireCrawl scrape模式（html）成功")
                            return result.html
                        elif hasattr(result, 'content') and result.content:
                            print(f"[INFO] FireCrawl scrape模式（content）成功")
                            return result.content
                        # 如果是字典格式
                        elif isinstance(result, dict):
                            if 'markdown' in result and result['markdown']:
                                print(f"[INFO] FireCrawl scrape模式（dict markdown）成功")
                                return result['markdown']
                            elif 'html' in result and result['html']:
                                print(f"[INFO] FireCrawl scrape模式（dict html）成功")
                                return result['html']
                            elif 'content' in result and result['content']:
                                print(f"[INFO] FireCrawl scrape模式（dict content）成功")
                                return result['content']
                except Exception as e:
                    print(f"[WARN] FireCrawl scrape模式（新格式）失败: {e}")

                # 尝试只使用markdown格式
                try:
                    result = app.scrape_url(url, formats=['markdown'])

                    if result:
                        if hasattr(result, 'markdown') and result.markdown:
                            print(f"[INFO] FireCrawl scrape模式（仅markdown）成功")
                            return result.markdown
                        elif isinstance(result, dict) and 'markdown' in result:
                            print(f"[INFO] FireCrawl scrape模式（仅markdown dict）成功")
                            return result['markdown']
                except Exception as e:
                    print(f"[WARN] FireCrawl scrape模式（仅markdown）失败: {e}")

                # 最后尝试不带格式参数的调用
                try:
                    result = app.scrape_url(url)

                    if result:
                        if hasattr(result, 'markdown') and result.markdown:
                            print(f"[INFO] FireCrawl scrape模式（默认）成功")
                            return result.markdown
                        elif hasattr(result, 'content') and result.content:
                            print(f"[INFO] FireCrawl scrape模式（默认content）成功")
                            return result.content
                        elif isinstance(result, dict):
                            if 'markdown' in result and result['markdown']:
                                print(f"[INFO] FireCrawl scrape模式（默认dict）成功")
                                return result['markdown']
                            elif 'content' in result and result['content']:
                                print(f"[INFO] FireCrawl scrape模式（默认dict content）成功")
                                return result['content']
                except Exception as e:
                    print(f"[WARN] FireCrawl scrape模式（默认）失败: {e}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    print(f"[INFO] FireCrawl第 {attempt + 1} 次失败，等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)

            except Exception as e:
                print(f"[ERROR] FireCrawl第 {attempt + 1} 次尝试异常: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"[INFO] 等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)

        print(f"[ERROR] FireCrawl所有 {max_retries} 次尝试都失败")
        return ""

    except ImportError:
        print("[ERROR] FireCrawl库未安装，请运行: pip install firecrawl-py")
        return ""
    except Exception as e:
        print(f"[ERROR] FireCrawl初始化失败: {e}")
        return ""


def _try_zyte(url: str, api_config: Dict[str, Any], max_retries: int = 3) -> str:
    """尝试使用Zyte抓取内容"""
    try:
        zyte_api_key = api_config.get('zyte_api_key', '')
        if not zyte_api_key or zyte_api_key.startswith('YOUR_'):
            print("[WARN] Zyte API密钥未配置，跳过Zyte抓取")
            return ""

        # 创建Zyte客户端
        zyte_client = create_zyte_client(zyte_api_key)
        if not zyte_client:
            print("[ERROR] Zyte客户端创建失败")
            return ""

        # 使用Zyte抓取内容
        content = zyte_client.extract_content(url, max_retries=max_retries)
        return content or ""

    except Exception as e:
        print(f"[ERROR] Zyte抓取异常: {e}")
        return ""


class NewsProcessor:
    """新闻处理器 - 负责新闻的评估、获取和优化处理"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化新闻处理器"""
        self.config = config
        self.ai_analyzer = AIContentAnalyzer(config)
        self.deduplicator = NewsDeduplicator(similarity_threshold=0.6)
        
    def process_news_batch(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理新闻"""
        if not news_list:
            print("[WARN] 没有新闻需要处理")
            return []

        print(f"[INFO] 开始批量处理 {len(news_list)} 条新闻")

        # 步骤0: 新闻去重合并
        deduplicated_news = self.deduplicator.deduplicate_and_merge(news_list)

        # 步骤1: AI评估筛选
        relevant_news = self.evaluate_news_relevance(deduplicated_news)

        if not relevant_news:
            print("[WARN] 没有新闻通过AI评估")
            return []

        # 步骤2: 按AI评分排序，只保留前N条新闻
        top_news = self.select_top_news_by_score(relevant_news)

        if not top_news:
            print("[WARN] 没有新闻进入最终推送列表")
            return []

        # 步骤3: 只对最终保留的新闻获取完整内容
        content_news = self.fetch_full_content_batch(top_news)

        # 步骤4: AI优化和翻译
        processed_news = self.optimize_and_translate_batch(content_news)

        print(f"[INFO] 批量处理完成，共 {len(processed_news)} 条新闻准备发布")
        return processed_news
    
    def evaluate_news_relevance(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """评估新闻相关性"""
        print("[INFO] 步骤1：统一AI评估所有新闻...")
        relevant_news = []
        min_score = self.config.get('ai_settings', {}).get('min_relevance_score', 6)
        
        for i, news_item in enumerate(news_list, 1):
            try:
                source_type = news_item.get('source_type', 'Unknown')
                title = news_item.get('title', '')[:50]
                print(f"[INFO] AI评估第 {i}/{len(news_list)} 条新闻 ({source_type}): {title}...")
                
                # 使用新的AI评估方法
                evaluation_result = self.ai_analyzer.evaluate_news_relevance([news_item])

                if evaluation_result and len(evaluation_result) > 0:
                    evaluated_news = evaluation_result[0]
                    is_relevant = evaluated_news.get('is_relevant', False)
                    score = evaluated_news.get('relevance_score', 0)
                else:
                    is_relevant = False
                    score = 0
                
                if is_relevant and score >= min_score:
                    # 保存AI评分到新闻项中
                    news_item['ai_score'] = score
                    relevant_news.append(news_item)
                    print(f"[INFO] 新闻 {i} AI评估通过 (评分: {score:.2f})")
                else:
                    print(f"[INFO] 新闻 {i} AI评估不通过 (评分: {score:.2f})，跳过")
                    
            except Exception as e:
                print(f"[ERROR] 新闻 {i} AI评估失败: {str(e)}")
                continue
        
        print(f"[INFO] AI评估完成，{len(relevant_news)}/{len(news_list)} 条新闻通过评估")
        return relevant_news

    def select_top_news_by_score(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按AI评分排序，选择排名前N的新闻"""
        if not news_list:
            return []

        max_send_limit = self.config.get('max_send_limit', 10)
        print(f"[INFO] 步骤2：按AI评分排序，选择前 {max_send_limit} 条新闻...")

        # 按AI评分降序排序
        sorted_news = sorted(news_list, key=lambda x: x.get('ai_score', 0), reverse=True)

        # 只保留前N条
        top_news = sorted_news[:max_send_limit]

        print(f"[INFO] 评分排序结果:")
        for i, news in enumerate(top_news, 1):
            title = news.get('title', '')[:40]
            score = news.get('ai_score', 0)
            source = news.get('source_type', 'Unknown')
            print(f"  {i:2d}. [{source}] {title}... (评分: {score:.2f})")

        if len(sorted_news) > max_send_limit:
            print(f"[INFO] 共有 {len(sorted_news)} 条新闻通过评估，保留评分最高的 {len(top_news)} 条")
        else:
            print(f"[INFO] 共有 {len(top_news)} 条新闻进入最终处理")

        return top_news
    
    def fetch_full_content_batch(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量获取完整内容"""
        # 检查爬虫开关
        content_extraction_enabled = self.config.get('content_extraction', {}).get('enabled', True)

        if not content_extraction_enabled:
            print(f"[INFO] 步骤3：内容抓取已禁用，跳过FireCrawl+Zyte抓取，直接使用原始内容...")
            processed_news = []
            for i, news_item in enumerate(news_list, 1):
                # 使用原始内容作为raw_content
                fallback_content = (news_item.get('content', '') or
                                  news_item.get('description', '') or
                                  news_item.get('summary', ''))
                news_item['raw_content'] = fallback_content
                processed_news.append(news_item)
                title = news_item.get('title', '')[:50]
                print(f"[INFO] 新闻 {i}/{len(news_list)} 使用原始内容: {title}... (长度: {len(fallback_content)})")

            print(f"[INFO] 原始内容处理完成，{len(processed_news)}/{len(news_list)} 条新闻处理完成")
            return processed_news

        print(f"[INFO] 步骤3：使用FireCrawl+Zyte备用机制获取 {len(news_list)} 条最终新闻的完整内容...")
        processed_news = []

        for i, news_item in enumerate(news_list, 1):
            try:
                title = news_item.get('title', '')[:50]
                print(f"[INFO] 内容抓取第 {i}/{len(news_list)} 条新闻: {title}...")

                api_config = {
                    'firecrawl_api_key': self.config.get('firecrawl_api_key', ''),
                    'zyte_api_key': self.config.get('zyte_api_key', '')
                }
                full_content = fetch_full_content_with_fallback(news_item.get("url", ""), api_config)

                if full_content:
                    news_item['raw_content'] = full_content
                    print(f"[INFO] 新闻 {i} 内容抓取成功，内容长度: {len(full_content)} 字符")
                else:
                    # 内容抓取失败时，按优先级使用原始内容
                    fallback_content = (news_item.get('content', '') or
                                      news_item.get('description', '') or
                                      news_item.get('summary', ''))
                    news_item['raw_content'] = fallback_content
                    print(f"[WARN] 新闻 {i} 内容抓取失败，使用原始内容 (长度: {len(fallback_content)})")

                processed_news.append(news_item)

            except Exception as e:
                # 即使出错也不丢弃新闻，按优先级使用原始内容
                fallback_content = (news_item.get('content', '') or
                                  news_item.get('description', '') or
                                  news_item.get('summary', ''))
                news_item['raw_content'] = fallback_content
                processed_news.append(news_item)
                print(f"[ERROR] 新闻 {i} FireCrawl获取出错: {str(e)}，使用原始内容 (长度: {len(fallback_content)})")

        print(f"[INFO] FireCrawl处理完成，{len(processed_news)}/{len(news_list)} 条新闻处理完成")
        return processed_news
    
    def optimize_and_translate_batch(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量AI优化和翻译"""
        print(f"[INFO] 步骤4：AI优化和翻译 {len(news_list)} 条新闻内容...")
        processed_news = []
        
        for i, news_item in enumerate(news_list, 1):
            try:
                title = news_item.get('title', '')[:50]
                print(f"[INFO] AI优化第 {i}/{len(news_list)} 条新闻: {title}...")
                
                # 使用AI优化和翻译内容
                raw_content = news_item.get('raw_content', '')
                original_link = news_item.get('url', '')
                
                optimized_result = self.ai_analyzer.optimize_and_translate_content(
                    raw_content, original_link
                )
                
                if optimized_result and isinstance(optimized_result, dict):
                    # 检查是否是AI标记的无效数据
                    if optimized_result.get("invalid_data", False):
                        print(f"[WARN] 新闻 {i} 被AI判定为无效数据，丢弃该新闻")
                        continue

                    # 验证AI优化结果的内容
                    opt_title = optimized_result.get("title", "").strip()
                    opt_content = optimized_result.get("content", "").strip()

                    if opt_title and opt_content:
                        # AI优化成功且内容完整
                        webhook_data = {
                            "message_type": optimized_result.get("message_type", "text"),
                            "title": opt_title,
                            "content": opt_content,
                            "original_link": optimized_result.get("original_link", original_link),
                            "ai_score": news_item.get('ai_score', 0.0)
                        }
                        processed_news.append(webhook_data)
                        print(f"[INFO] 新闻 {i} AI优化成功")
                    else:
                        # AI优化返回了结果但内容为空，直接丢弃新闻
                        print(f"[WARN] 新闻 {i} AI优化返回空内容，丢弃该新闻")
                        continue
                elif optimized_result is None:
                    # AI优化完全失败，直接丢弃新闻
                    print(f"[WARN] 新闻 {i} AI优化完全失败，丢弃该新闻")
                    continue
                else:
                    # AI优化返回了非字典结果，直接丢弃新闻
                    print(f"[WARN] 新闻 {i} AI优化返回异常结果，丢弃该新闻")
                    continue

            except Exception as e:
                print(f"[ERROR] 新闻 {i} 处理出错: {str(e)}")
                continue
        
        return processed_news


    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'ai_analyzer_ready': bool(self.ai_analyzer),
            'gemini_enabled': bool(self.config.get('gemini_api_keys')),
            'openrouter_enabled': bool(self.config.get('openrouter_api_keys')),
            'content_extraction_enabled': self.config.get('content_extraction', {}).get('enabled', True),
            'firecrawl_enabled': bool(self.config.get('firecrawl_api_key')),
            'zyte_enabled': bool(self.config.get('zyte_api_key')),
            'min_relevance_score': self.config.get('ai_settings', {}).get('min_relevance_score', 6)
        }


if __name__ == "__main__":
    # 测试代码
    from .config_manager import ConfigManager
    
    print("🧪 测试新闻处理器...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        processor = NewsProcessor(config)
        
        # 获取统计信息
        stats = processor.get_processing_stats()
        print("📊 处理器统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 新闻处理器初始化成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
