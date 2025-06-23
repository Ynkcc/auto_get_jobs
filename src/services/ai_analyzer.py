# src/services/ai_analyzer.py
import logging
import re
from openai import AsyncOpenAI, AsyncAzureOpenAI, OpenAIError

from ..common.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class AiAnalyzer:
    def __init__(self):
        config = ConfigManager.get_config()
        config_ai = config.ai
        config_greeting = config.application.greeting

        self.model = config_ai.model
        self.temperature = config_ai.temperature
        self.job_requirements_prompt = config_ai.job_requirements_prompt
        self.provider = config_ai.provider
        self.resume_file_name = config_ai.resume_for_ai_file
        self.resume_for_ai = self._load_user_requirements()
        self.ai_prompt = config_ai.prompt
        self.greeting_prompt = config_greeting.greeting_prompt
        
        self.client = self._initialize_client(config_ai)

    def _initialize_client(self, config_ai):
        """根据配置初始化 OpenAI 或 AzureOpenAI 客户端"""
        if self.provider == "azure":
            if not config_ai.api_version:
                raise ValueError("使用 Azure AI 服务时，必须在配置中指定 'api_version'")
            return AsyncAzureOpenAI(
                api_key=config_ai.api_key,
                azure_endpoint=config_ai.api_url,
                api_version=config_ai.api_version,
                max_retries=3,
            )
        elif self.provider == "openai":
            return AsyncOpenAI(
                api_key=config_ai.api_key,
                base_url=config_ai.api_url,
                max_retries=3,
            )
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")

    def _load_user_requirements(self):
        """从文件加载用户简历"""
        try:
            with open(self.resume_file_name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"未找到用于ai分析的简历文件 {self.resume_file_name}")
            return ""

    async def ai_greeting(self, job_detail):
        """生成AI打招呼语"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.greeting_prompt},
                {"role": "user", "content": f"目标职位关键要求：{job_detail}\n\n求职者真实简历：{self.resume_for_ai}"},
                {"role": "system", "content": "请生成符合上述要求的打招呼语，仅输出最终内容，不要用任何标记符号"}
            ],
            "temperature": self.temperature,
        }
        try:
            response = await self.client.chat.completions.create(**payload)
            return response.choices[0].message.content.strip()
        except OpenAIError as e:
            logger.error(f"AI生成打招呼语失败: {e}")
            return None

    async def ai_hr_check(self, job_detail):
        """使用AI分析职位是否匹配"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.ai_prompt},
                {"role": "user", "content": f"岗位要求：{job_detail}"},
                {"role": "user", "content": f"用户简历：{self.resume_for_ai}"},
                {"role": "user", "content": f"用户对工作岗位的要求：{self.job_requirements_prompt}"}
            ],
            "temperature": self.temperature,
        }
        try:
            response = await self.client.chat.completions.create(**payload)
            origin_content = response.choices[0].message.content.lower()
            match = re.match(r"<think>(.*?)</think>(.*)", origin_content, re.DOTALL)
            ai_think = match.group(1).strip() if match else ""
            content = match.group(2) if match else origin_content
            return "true" in content, ai_think
        except OpenAIError as e:
            logger.error(f"AI分析失败: {e}")
            return False, f"AI分析异常: {e}"

    async def close(self):
        """关闭 aiohttp.ClientSession"""
        if self.client:
            await self.client.aclose()
            logger.info("AiAnalyzer的OpenAI客户端会话已关闭。")