#!/usr/bin/env python3
"""
AI内容分析器 - 重构版本
支持豆包和Gemini AI进行新闻评估和内容优化
支持AI首选项配置和联网搜索功能
"""

import json
import time
import requests
import random
from typing import Dict, Any, List, Optional


class AIContentAnalyzer:
    """AI内容分析器 - 重构版本"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI分析器

        Args:
            config: 完整的配置字典
        """
        self.config = config

        # AI首选项配置
        self.ai_preference = config.get('ai_preference', ['openrouter', 'gemini'])

        # Gemini配置（支持多API）
        self.gemini_api_keys = config.get('gemini_api_keys', [])
        self.gemini_model = config.get('gemini_model', 'gemini-2.5-flash')
        self.gemini_enable_search = config.get('gemini_enable_search', True)

        # OpenRouter配置（支持多API）
        self.openrouter_api_keys = config.get('openrouter_api_keys', [])
        self.openrouter_endpoint = config.get('openrouter_endpoint', 'https://openrouter.ai/api/v1')
        self.openrouter_model = config.get('openrouter_model', 'deepseek/deepseek-r1-0528:free')
        self.openrouter_enable_search = config.get('openrouter_enable_search', False)

        # 从配置中获取提示词
        ai_settings = config.get('ai_settings', {})
        prompts = ai_settings.get('prompts', {})
        self.evaluation_prompt = prompts.get('evaluation_prompt', '')
        self.optimization_prompt = prompts.get('optimization_prompt', '')

        print(f"[INFO] AI首选项: {self.ai_preference}")
        print(f"[INFO] Gemini API数量: {len(self.gemini_api_keys)}, 联网搜索: {'启用' if self.gemini_enable_search else '禁用'}")
        print(f"[INFO] OpenRouter API数量: {len(self.openrouter_api_keys)}, 联网搜索: {'启用' if self.openrouter_enable_search else '禁用'}")

    def _get_random_gemini_api_key(self) -> str:
        """随机选择一个Gemini API密钥"""
        if not self.gemini_api_keys:
            return ""
        selected_key = random.choice(self.gemini_api_keys)
        print(f"[INFO] 随机选择Gemini API: {selected_key[:20]}...")
        return selected_key

    def _get_random_openrouter_api_key(self) -> str:
        """随机选择一个OpenRouter API密钥"""
        if not self.openrouter_api_keys:
            return ""
        selected_key = random.choice(self.openrouter_api_keys)
        print(f"[INFO] 随机选择OpenRouter API: {selected_key[:20]}...")
        return selected_key

    def _extract_json(self, text: str):
        """去除AI响应中的代码块标记并解析JSON"""
        import re

        try:
            print(f"[DEBUG] 原始AI响应: {text[:200]}...")

            # 去除```json ... ```或``` ... ```包裹
            cleaned = re.sub(r'^```json|^```|```$', '', text.strip(), flags=re.MULTILINE).strip()

            print(f"[DEBUG] 清理后文本: {cleaned[:200]}...")

            # 查找JSON对象的开始和结束位置
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                # 提取JSON部分
                json_str = cleaned[start_idx:end_idx + 1]
                print(f"[DEBUG] 提取的JSON: {json_str}")

                # 检查JSON是否完整
                if json_str.count('{') != json_str.count('}'):
                    print(f"[WARN] JSON括号不匹配，可能被截断")
                    return None

                return json.loads(json_str)
            else:
                print(f"[WARN] 未找到完整的JSON对象")
                # 如果没有找到完整的JSON对象，尝试直接解析
                return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析失败: {e}")
            print(f"[ERROR] 原始文本: {text[:500]}...")
            return None
        except Exception as e:
            print(f"[ERROR] JSON提取异常: {e}")
            print(f"[ERROR] 原始文本: {text[:500]}...")
            return None

    def evaluate_news_relevance(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估新闻相关性

        Args:
            news_list: 新闻列表

        Returns:
            评估后的新闻列表
        """
        print(f"[INFO] 开始AI评估 {len(news_list)} 条新闻的相关性...")

        evaluated_news = []

        for i, news in enumerate(news_list, 1):
            print(f"[INFO] 评估第 {i}/{len(news_list)} 条新闻...")

            # 轮询机制：首选AI → 备选AI → 首选AI → 备选AI，总共4次
            result = None
            max_total_attempts = 4

            for attempt in range(max_total_attempts):
                # 轮询选择AI：偶数次(0,2)用首选，奇数次(1,3)用备选
                ai_index = attempt % len(self.ai_preference)
                ai_name = self.ai_preference[ai_index]

                # 计算这是该AI的第几次尝试
                ai_attempt_count = (attempt // len(self.ai_preference)) + 1

                # 添加延迟避免频繁调用（第一次不延迟）
                if attempt > 0:
                    delay_seconds = 2  # 2秒延迟
                    print(f"[INFO] 等待{delay_seconds}秒后进行下次尝试...")
                    time.sleep(delay_seconds)

                try:
                    print(f"[INFO] 轮询第{attempt+1}/4次: 尝试{ai_name.upper()}评估 (该AI第{ai_attempt_count}次)")

                    if ai_name == 'openrouter':
                        result = self._evaluate_with_openrouter(news)
                    elif ai_name == 'gemini':
                        result = self._evaluate_with_gemini(news)

                    if result:
                        print(f"[INFO] {ai_name.upper()}评估成功 (轮询第{attempt+1}次)")
                        break
                    else:
                        print(f"[WARN] {ai_name.upper()}评估失败 (轮询第{attempt+1}次)")

                except Exception as e:
                    print(f"[ERROR] {ai_name.upper()}评估异常 (轮询第{attempt+1}次): {e}")

            if result:
                # 添加评估结果到新闻
                score = result.get('relevance_score', 0.0)
                is_relevant = result.get('is_relevant', False)
                news.update(result)
                evaluated_news.append(news)

                # 详细的调试信息
                title_preview = news.get('title', '')[:50]
                content_preview = self._get_content_for_evaluation(news)[:100]
                print(f"[INFO] 新闻 {i} 评估成功")
                print(f"[DEBUG] 标题: {title_preview}...")
                print(f"[DEBUG] 内容预览: {content_preview}...")
                print(f"[DEBUG] 评分: {score}, 相关性: {is_relevant}")

                # 如果评分异常高，额外警告
                full_text = (news.get('title', '') + ' ' + self._get_content_for_evaluation(news)).lower()
                plant_keywords = ['植物', '提取物', '保健品', '功能性', '活性成分', '膳食补充剂', '营养', '健康', 'fda', 'efsa']
                has_relevant_keywords = any(keyword in full_text for keyword in plant_keywords)

                if score >= 8 and not has_relevant_keywords:
                    print(f"[WARN] ⚠️ 异常高分警告：非植物提取物相关新闻获得高分 {score}")
                    print(f"[WARN] 请检查AI评估逻辑是否正确")
                    print(f"[DEBUG] 全文关键词检查: {full_text[:200]}...")

            else:
                print(f"[WARN] 新闻 {i} 所有AI评估都失败，跳过")

        print(f"[INFO] AI评估完成，{len(evaluated_news)}/{len(news_list)} 条新闻评估成功")
        return evaluated_news

    def optimize_and_translate_content(self, raw_content: str, original_link: str) -> Optional[Dict[str, Any]]:
        """
        优化和翻译内容

        Args:
            raw_content: 原始内容
            original_link: 原始链接

        Returns:
            优化后的内容字典
        """
        print(f"[INFO] 开始AI内容优化和翻译...")

        # 轮询机制：首选AI → 备选AI → 首选AI → 备选AI，总共4次
        max_total_attempts = 4

        for attempt in range(max_total_attempts):
            # 轮询选择AI：偶数次(0,2)用首选，奇数次(1,3)用备选
            ai_index = attempt % len(self.ai_preference)
            ai_name = self.ai_preference[ai_index]

            # 计算这是该AI的第几次尝试
            ai_attempt_count = (attempt // len(self.ai_preference)) + 1

            # 添加延迟避免频繁调用（第一次不延迟）
            if attempt > 0:
                delay_seconds = 2  # 2秒延迟
                print(f"[INFO] 等待{delay_seconds}秒后进行下次尝试...")
                time.sleep(delay_seconds)

            try:
                print(f"[INFO] 轮询第{attempt+1}/4次: 尝试{ai_name.upper()}内容优化 (该AI第{ai_attempt_count}次)")

                if ai_name == 'openrouter':
                    result = self._optimize_with_openrouter(raw_content, original_link)
                elif ai_name == 'gemini':
                    result = self._optimize_with_gemini(raw_content, original_link)

                if result:
                    print(f"[INFO] {ai_name.upper()}内容优化成功 (轮询第{attempt+1}次)")
                    return result
                else:
                    print(f"[WARN] {ai_name.upper()}内容优化失败 (轮询第{attempt+1}次)")

            except Exception as e:
                print(f"[ERROR] {ai_name.upper()}内容优化异常 (轮询第{attempt+1}次): {e}")

        print(f"[ERROR] 所有AI内容优化都失败")
        return None

    def _get_content_for_evaluation(self, news: Dict[str, Any]) -> str:
        """获取用于AI评估的内容，按优先级选择可用字段"""
        # 优先级：content > description > summary > 空字符串
        content = news.get('content', '').strip()
        if content:
            print(f"[DEBUG] 使用content字段进行评估 (长度: {len(content)})")
            return content

        description = news.get('description', '').strip()
        if description:
            print(f"[DEBUG] 使用description字段进行评估 (长度: {len(description)})")
            return description

        summary = news.get('summary', '').strip()
        if summary:
            print(f"[DEBUG] 使用summary字段进行评估 (长度: {len(summary)})")
            return summary

        # 如果都没有内容，返回空字符串，让AI基于标题进行评估
        print(f"[WARN] 没有可用内容，仅基于标题进行AI评估")
        return ''

    def _evaluate_with_openrouter(self, news: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用OpenRouter评估新闻"""
        try:
            # 随机选择API密钥
            api_key = self._get_random_openrouter_api_key()
            if not api_key:
                print("[ERROR] 没有可用的OpenRouter API密钥")
                return None

            # 构建评估提示词 - 使用可用的内容字段
            content_for_evaluation = self._get_content_for_evaluation(news)
            prompt = self.evaluation_prompt.format(
                title=news.get('title', ''),
                content=content_for_evaluation,
                link=news.get('url', news.get('link', ''))
            )

            # 构建请求数据
            request_data = {
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                f"{self.openrouter_endpoint}/chat/completions",
                headers=headers,
                json=request_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] OpenRouter评估响应: {result}")
                if 'choices' in result and len(result['choices']) > 0:
                    text = result['choices'][0]['message']['content']
                    return self._extract_json(text)
                else:
                    print(f"[ERROR] OpenRouter评估响应格式异常: {result}")
            else:
                print(f"[ERROR] OpenRouter评估API错误: {response.status_code} - {response.text}")

            return None

        except Exception as e:
            print(f"[ERROR] OpenRouter评估失败: {e}")
            return None



    def _evaluate_with_gemini(self, news: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用Gemini评估新闻"""
        try:
            # 随机选择API密钥
            api_key = self._get_random_gemini_api_key()
            if not api_key:
                print("[ERROR] 没有可用的Gemini API密钥")
                return None

            # 构建评估提示词 - 使用可用的内容字段
            content_for_evaluation = self._get_content_for_evaluation(news)
            prompt = self.evaluation_prompt.format(
                title=news.get('title', ''),
                content=content_for_evaluation,
                link=news.get('url', news.get('link', ''))
            )

            # 构建请求数据
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4000
                }
            }

            # 暂时禁用Gemini联网搜索，避免token超限
            # if self.gemini_enable_search:
            #     request_data["tools"] = [
            #         {
            #             "googleSearch": {}
            #         }
            #     ]

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={api_key}"

            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] Gemini响应: {result}")
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0]['text']
                        return self._extract_json(text)
                    else:
                        print(f"[ERROR] Gemini响应格式异常: {candidate}")
            else:
                print(f"[ERROR] Gemini API错误: {response.status_code} - {response.text}")

            return None

        except Exception as e:
            print(f"[ERROR] Gemini评估失败: {e}")
            return None

    def _optimize_with_openrouter(self, raw_content: str, original_link: str) -> Optional[Dict[str, Any]]:
        """使用OpenRouter优化内容"""
        try:
            # 随机选择API密钥
            api_key = self._get_random_openrouter_api_key()
            if not api_key:
                print("[ERROR] 没有可用的OpenRouter API密钥")
                return None

            # 构建优化提示词
            prompt = self.optimization_prompt.format(
                raw_content=raw_content,
                original_link=original_link
            )

            # 构建请求数据
            request_data = {
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                f"{self.openrouter_endpoint}/chat/completions",
                headers=headers,
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] OpenRouter优化响应: {result}")
                if 'choices' in result and len(result['choices']) > 0:
                    text = result['choices'][0]['message']['content']
                    return self._extract_json(text)
                else:
                    print(f"[ERROR] OpenRouter优化响应格式异常: {result}")
            else:
                print(f"[ERROR] OpenRouter优化API错误: {response.status_code} - {response.text}")

            return None

        except Exception as e:
            print(f"[ERROR] OpenRouter优化失败: {e}")
            return None



    def _optimize_with_gemini(self, raw_content: str, original_link: str) -> Optional[Dict[str, Any]]:
        """使用Gemini优化内容"""
        try:
            # 随机选择API密钥
            api_key = self._get_random_gemini_api_key()
            if not api_key:
                print("[ERROR] 没有可用的Gemini API密钥")
                return None

            # 构建优化提示词
            prompt = self.optimization_prompt.format(
                raw_content=raw_content,
                original_link=original_link
            )

            # 构建请求数据
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4000
                }
            }

            # 如果启用搜索，添加搜索工具
            if self.gemini_enable_search:
                request_data["tools"] = [
                    {
                        "googleSearch": {}
                    }
                ]

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={api_key}"

            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] Gemini优化响应: {result}")
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                        text = candidate['content']['parts'][0]['text']
                        return self._extract_json(text)
                    else:
                        print(f"[ERROR] Gemini优化响应格式异常: {candidate}")
                else:
                    print(f"[ERROR] Gemini优化响应无candidates: {result}")
            else:
                print(f"[ERROR] Gemini优化API错误: {response.status_code} - {response.text}")

            return None

        except Exception as e:
            print(f"[ERROR] Gemini优化失败: {e}")
            return None