import logging
import os
import asyncio
import re

import aiohttp

from utils.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class AiAnalyzer:
    def __init__(self):
        config_ai = ConfigManager.get_config().ai
        self.api_url = config_ai.api_url
        self.api_key = config_ai.api_key
        self.model = config_ai.model
        self.temperature = config_ai.temperature
        self.provider = config_ai.provider
        self.resume_file_name = config_ai.resume_for_ai_file
        self.resume_for_ai = self._load_user_requirements()
        self.ai_prompt = config_ai.prompt
        self.headers = self._get_provider_handlers()

    def _load_user_requirements(self):
        """从文件加载用户简历"""
        try:
            with open(self.resume_file_name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"未找到用于ai分析的简历文件 {self.resume_file_name}")
            return ""

    def _get_provider_handlers(self):
        """处理不同提供商的请求差异"""
        if self.provider == "azure":
            headers = {
                "api-key": f"{self.api_key}",
                "Content-Type": "application/json"
            }
            return headers
        elif self.provider == "openai":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            return headers
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")

    async def ai_hr_check(self, job_detail):
        for attempt in range(5):
            try:
                async with aiohttp.ClientSession() as session:
                    # 构建请求体
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.ai_prompt},
                            {"role": "user", "content": f"岗位要求：{job_detail}"},
                            {"role":"user","content":f"用户简历、要求：{self.resume_for_ai}"}
                        ],
                        "temperature": self.temperature,
                        #"max_tokens": 50 DeepSeek-R1包含思考过程，max_tokens太低会使回答不完整
                    }

                    async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload,
                        timeout=30
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

                        origin_content = data['choices'][0]['message']['content'].lower()
                        match = re.match(
                            r"<think>(.*?)</think>(.*)",
                            origin_content,
                            re.DOTALL
                        )
                        ai_think = None
                        if match:
                            ai_think = match.group(1)
                            content = match.group(2)
                        else:
                            content = origin_content
                        check_result = "true" in content
                        return check_result, ai_think

            except aiohttp.ClientError as e:
                logger.warning(f"网络请求失败 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(2 ** attempt)
            except KeyError as e:
                logger.error(f"响应格式错误: {str(e)}")
                break
            except TimeoutError as e:
                logger.warning(f"AI连接超时 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"AI分析失败 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(1)

        return False