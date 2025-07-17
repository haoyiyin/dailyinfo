#!/usr/bin/env python3
"""
Zyte API客户端
用作FireCrawl的备用抓取工具
"""

import requests
import time
import json
from typing import Dict, Any, Optional


class ZyteClient:
    """Zyte API客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.zyte.com/v1/extract"
        self.session = requests.Session()
        self.session.auth = (api_key, '')
        
    def extract_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        使用Zyte API提取网页内容
        
        Args:
            url: 要抓取的URL
            max_retries: 最大重试次数
            
        Returns:
            提取的内容，失败返回None
        """
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Zyte抓取尝试第 {attempt + 1}/{max_retries} 次: {url}")
                
                # 构建请求数据 - 使用正确的Zyte API格式
                request_data = {
                    "url": url,
                    "article": True
                }
                
                # 发送请求
                response = self.session.post(
                    self.base_url,
                    json=request_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 提取文章内容
                    content = self._extract_article_content(result)
                    
                    if content:
                        print(f"[INFO] Zyte抓取成功，内容长度: {len(content)} 字符")
                        return content
                    else:
                        print(f"[WARN] Zyte抓取成功但未提取到有效内容")
                        
                elif response.status_code == 422:
                    print(f"[WARN] Zyte API请求参数错误: {response.text}")
                    break  # 参数错误不重试
                    
                elif response.status_code == 429:
                    print(f"[WARN] Zyte API请求频率限制，等待重试...")
                    time.sleep(5 * (attempt + 1))  # 指数退避
                    
                else:
                    print(f"[WARN] Zyte API请求失败: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"[WARN] Zyte API请求超时")
                
            except requests.exceptions.RequestException as e:
                print(f"[WARN] Zyte API网络错误: {e}")
                
            except Exception as e:
                print(f"[ERROR] Zyte API未知错误: {e}")
            
            # 重试前等待
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                print(f"[INFO] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"[ERROR] Zyte抓取失败，已重试 {max_retries} 次")
        return None
    
    def _extract_article_content(self, result: Dict[str, Any]) -> Optional[str]:
        """从Zyte API结果中提取文章内容"""
        try:
            # 优先使用article字段
            if 'article' in result and result['article']:
                article = result['article']
                
                # 提取文章正文
                if 'articleBody' in article and article['articleBody']:
                    return article['articleBody']
                
                # 如果没有正文，尝试提取其他内容
                if 'headline' in article and 'description' in article:
                    headline = article.get('headline', '')
                    description = article.get('description', '')
                    return f"{headline}\n\n{description}"
            
            # 备选：使用httpResponseBody
            if 'httpResponseBody' in result and result['httpResponseBody']:
                html_content = result['httpResponseBody']
                # 简单的HTML清理（可以后续优化）
                return self._clean_html_content(html_content)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] 解析Zyte结果失败: {e}")
            return None
    
    def _clean_html_content(self, html_content: str) -> str:
        """简单的HTML内容清理"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本
            text = soup.get_text()
            
            # 清理空白字符
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except ImportError:
            print("[WARN] BeautifulSoup未安装，返回原始HTML")
            return html_content
        except Exception as e:
            print(f"[ERROR] HTML清理失败: {e}")
            return html_content
    
    def test_connection(self) -> bool:
        """测试Zyte API连接"""
        try:
            test_url = "https://httpbin.org/html"
            result = self.extract_content(test_url, max_retries=1)
            return result is not None
            
        except Exception as e:
            print(f"[ERROR] Zyte连接测试失败: {e}")
            return False


def create_zyte_client(api_key: str) -> Optional[ZyteClient]:
    """创建Zyte客户端"""
    if not api_key or api_key.startswith('YOUR_'):
        print("[WARN] Zyte API密钥未配置")
        return None
    
    try:
        client = ZyteClient(api_key)
        print("[INFO] Zyte客户端初始化成功")
        return client
        
    except Exception as e:
        print(f"[ERROR] Zyte客户端初始化失败: {e}")
        return None
