#!/usr/bin/env python3
"""
新闻去重合并器 - 检测相似新闻并合并内容
"""

from typing import List, Dict, Any, Tuple
import re
from difflib import SequenceMatcher
from collections import defaultdict


class NewsDeduplicator:
    """新闻去重合并器"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        初始化去重器
        
        Args:
            similarity_threshold: 相似度阈值，超过此值认为是重复新闻
        """
        self.similarity_threshold = similarity_threshold
        
    def deduplicate_and_merge(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重并合并相似新闻
        
        Args:
            news_list: 新闻列表
            
        Returns:
            去重后的新闻列表
        """
        if not news_list:
            return []
        
        print(f"[INFO] 开始新闻去重，原始数量: {len(news_list)}")
        
        # 步骤1: 找出相似新闻组
        similar_groups = self._find_similar_groups(news_list)
        
        # 步骤2: 合并每组相似新闻
        merged_news = []
        processed_indices = set()
        
        for group in similar_groups:
            if len(group) > 1:
                # 合并相似新闻
                merged_item = self._merge_similar_news([news_list[i] for i in group])
                merged_news.append(merged_item)
                processed_indices.update(group)
                
                titles = [news_list[i].get('title', '')[:30] for i in group]
                print(f"[INFO] 合并 {len(group)} 条相似新闻: {titles}")
            else:
                # 单独的新闻，直接添加
                merged_news.append(news_list[group[0]])
                processed_indices.add(group[0])
        
        # 添加未处理的新闻
        for i, news in enumerate(news_list):
            if i not in processed_indices:
                merged_news.append(news)
        
        print(f"[INFO] 去重完成，最终数量: {len(merged_news)}")
        return merged_news
    
    def _find_similar_groups(self, news_list: List[Dict[str, Any]]) -> List[List[int]]:
        """找出相似新闻组"""
        groups = []
        processed = set()
        
        for i, news1 in enumerate(news_list):
            if i in processed:
                continue
                
            current_group = [i]
            processed.add(i)
            
            for j, news2 in enumerate(news_list[i+1:], i+1):
                if j in processed:
                    continue
                    
                similarity = self._calculate_similarity(news1, news2)
                if similarity >= self.similarity_threshold:
                    current_group.append(j)
                    processed.add(j)
            
            groups.append(current_group)
        
        return groups
    
    def _calculate_similarity(self, news1: Dict[str, Any], news2: Dict[str, Any]) -> float:
        """计算两条新闻的相似度"""
        # 获取标题和内容
        title1 = self._clean_text(news1.get('title', ''))
        title2 = self._clean_text(news2.get('title', ''))
        content1 = self._clean_text(news1.get('description', '') or news1.get('content', ''))
        content2 = self._clean_text(news2.get('description', '') or news2.get('content', ''))
        
        # 计算标题相似度（权重70%）
        title_similarity = self._text_similarity(title1, title2)
        
        # 计算内容相似度（权重30%）
        content_similarity = self._text_similarity(content1, content2)
        
        # 综合相似度
        overall_similarity = title_similarity * 0.7 + content_similarity * 0.3
        
        return overall_similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _clean_text(self, text: str) -> str:
        """清理文本，去除特殊字符和多余空格"""
        if not text:
            return ""
        
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 去除特殊字符，保留字母、数字、空格
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 去除多余空格
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _merge_similar_news(self, similar_news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并相似新闻"""
        if not similar_news:
            return {}
        
        if len(similar_news) == 1:
            return similar_news[0]
        
        # 选择最完整的新闻作为基础
        base_news = self._select_best_news(similar_news)
        
        # 合并标题（选择最长的）
        merged_title = self._merge_titles([news.get('title', '') for news in similar_news])
        
        # 合并内容
        merged_content = self._merge_contents(similar_news)
        
        # 合并来源信息
        merged_sources = self._merge_sources(similar_news)
        
        # 选择最可靠的链接
        merged_url = self._select_best_url(similar_news)
        
        # 创建合并后的新闻
        merged_news = base_news.copy()
        merged_news.update({
            'title': merged_title,
            'description': merged_content,
            'content': merged_content,
            'url': merged_url,
            'source': f"合并来源: {merged_sources}",
            'source_type': 'Merged',
            'merged_count': len(similar_news),
            'original_sources': [news.get('source', '') for news in similar_news]
        })
        
        return merged_news
    
    def _select_best_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳新闻作为合并基础"""
        # 优先级：内容长度 > 来源可靠性 > 时间新旧
        best_news = news_list[0]
        best_score = 0
        
        for news in news_list:
            score = 0
            
            # 内容长度评分
            content = news.get('description', '') or news.get('content', '')
            score += len(content) * 0.01
            
            # 来源可靠性评分
            source = news.get('source', '').lower()
            if any(reliable in source for reliable in ['fda', 'efsa', 'nature', 'nutraceuticals']):
                score += 50
            elif any(good in source for good in ['food', 'health', 'science']):
                score += 20
            
            # URL可靠性评分
            url = news.get('url', '')
            if any(domain in url for domain in ['.gov', '.edu', 'nature.com']):
                score += 30
            
            if score > best_score:
                best_score = score
                best_news = news
        
        return best_news
    
    def _merge_titles(self, titles: List[str]) -> str:
        """合并标题，选择最完整的"""
        if not titles:
            return ""
        
        # 去除空标题
        valid_titles = [title.strip() for title in titles if title.strip()]
        
        if not valid_titles:
            return ""
        
        # 选择最长的标题
        return max(valid_titles, key=len)
    
    def _merge_contents(self, news_list: List[Dict[str, Any]]) -> str:
        """合并内容，去重并保留最完整的信息"""
        contents = []
        
        for news in news_list:
            content = news.get('description', '') or news.get('content', '')
            if content and content.strip():
                contents.append(content.strip())
        
        if not contents:
            return ""
        
        # 如果只有一个内容，直接返回
        if len(contents) == 1:
            return contents[0]
        
        # 选择最长的内容作为主要内容
        main_content = max(contents, key=len)
        
        # 检查其他内容是否有额外信息
        additional_info = []
        for content in contents:
            if content != main_content and len(content) > 50:
                # 检查是否包含主要内容中没有的关键信息
                if self._has_additional_info(main_content, content):
                    additional_info.append(content)
        
        # 合并内容
        if additional_info:
            merged = main_content + "\n\n补充信息：" + " | ".join(additional_info[:2])  # 最多添加2个补充信息
            return merged
        else:
            return main_content
    
    def _has_additional_info(self, main_content: str, other_content: str) -> bool:
        """检查其他内容是否包含主要内容中没有的信息"""
        main_words = set(self._clean_text(main_content).lower().split())
        other_words = set(self._clean_text(other_content).lower().split())
        
        # 如果其他内容有超过30%的独特词汇，认为有额外信息
        unique_words = other_words - main_words
        return len(unique_words) / len(other_words) > 0.3 if other_words else False
    
    def _merge_sources(self, news_list: List[Dict[str, Any]]) -> str:
        """合并来源信息"""
        sources = []
        for news in news_list:
            source = news.get('source', '') or news.get('source_type', '')
            if source and source not in sources:
                sources.append(source)
        
        return ", ".join(sources[:3])  # 最多显示3个来源
    
    def _select_best_url(self, news_list: List[Dict[str, Any]]) -> str:
        """选择最可靠的URL"""
        urls = [news.get('url', '') for news in news_list if news.get('url')]
        
        if not urls:
            return ""
        
        # 优先选择权威域名
        for url in urls:
            if any(domain in url for domain in ['.gov', '.edu', 'nature.com', 'fda.gov', 'efsa.europa.eu']):
                return url
        
        # 其次选择专业媒体
        for url in urls:
            if any(domain in url for domain in ['nutraceuticals', 'fooddive', 'wholefoodsmagazine']):
                return url
        
        # 最后返回第一个URL
        return urls[0]


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试新闻去重合并器...")
    
    # 模拟相似新闻
    test_news = [
        {
            "title": "New Study Shows Benefits of Grape Seed Extract",
            "description": "A recent study published in Nature shows that grape seed extract has antioxidant properties.",
            "url": "https://example1.com",
            "source": "Nature"
        },
        {
            "title": "Study: Grape Seed Extract Shows Antioxidant Benefits",
            "description": "Research published in Nature demonstrates the antioxidant effects of grape seed extract in clinical trials.",
            "url": "https://example2.com",
            "source": "Health News"
        },
        {
            "title": "FDA Approves New Dietary Supplement Regulations",
            "description": "The FDA has announced new regulations for dietary supplements.",
            "url": "https://fda.gov/news",
            "source": "FDA"
        }
    ]
    
    deduplicator = NewsDeduplicator(similarity_threshold=0.7)
    merged_news = deduplicator.deduplicate_and_merge(test_news)
    
    print(f"\n📊 测试结果:")
    print(f"原始新闻数量: {len(test_news)}")
    print(f"去重后数量: {len(merged_news)}")
    
    for i, news in enumerate(merged_news, 1):
        print(f"\n新闻 {i}:")
        print(f"  标题: {news.get('title', '')}")
        print(f"  来源: {news.get('source', '')}")
        if news.get('merged_count', 0) > 1:
            print(f"  合并数量: {news.get('merged_count')} 条")
            print(f"  原始来源: {news.get('original_sources', [])}")
