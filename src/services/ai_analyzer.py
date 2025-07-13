# src/services/ai_analyzer.py
import logging
import re
from openai import AsyncOpenAI, AsyncAzureOpenAI, OpenAIError
from pydantic import BaseModel
import instructor

from ..common.config_manager import ConfigManager, AiProvider

logger = logging.getLogger(__name__)

class AIAnalysisResult(BaseModel):
    match_conclusion: bool
    reasoning: str

class AiAnalyzer:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        config = ConfigManager.get_config()
        ai_config = config.ai
        
        # 查找当前激活的 provider
        active_provider_config = next((p for p in ai_config.providers if p.id == ai_config.active_ai_id), None)
        if not active_provider_config:
            raise ValueError(f"在配置中未找到激活的AI provider_id: {ai_config.active_ai_id}")

        self.active_provider: AiProvider = active_provider_config
        self.job_requirements_prompt = ai_config.job_requirements_prompt
        self.resume_for_ai = self._load_user_requirements(ai_config.resume_for_ai_file)
        self.ai_prompt = ai_config.prompt
        self.greeting_prompt = config.application.greeting.greeting_prompt
        
        base_client = self._initialize_client()
        self.client = instructor.patch(base_client, mode=instructor.Mode.JSON)

    def _initialize_client(self, provider: AiProvider = None):
        """根据指定的 provider 或激活的 provider 配置初始化客户端"""
        provider_to_use = provider or self.active_provider
        
        provider_type = provider_to_use.provider_type
        if provider_type == "azure":
            if not provider_to_use.api_version:
                raise ValueError("使用 Azure AI 服务时，必须在配置中指定 'api_version'")
            return AsyncAzureOpenAI(
                api_key=provider_to_use.api_key,
                azure_endpoint=provider_to_use.api_url,
                api_version=provider_to_use.api_version,
                max_retries=3,
            )
        elif provider_type == "openai":
            return AsyncOpenAI(
                api_key=provider_to_use.api_key,
                base_url=provider_to_use.api_url,
                max_retries=3,
            )
        else:
            raise ValueError(f"不支持的AI提供商: {provider_type}")


    def _load_user_requirements(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"未找到用于AI分析的简历文件 {file_name}")
            return ""

    async def test_provider(self, provider: AiProvider) -> (bool, str):
        """
        测试指定的AI服务商配置是否可用。
        返回一个元组 (是否成功, 消息)
        """
        try:
            test_client = self._initialize_client(provider)
            patched_client = instructor.patch(test_client, mode=instructor.Mode.JSON)
            
            logger.info(f"正在测试服务商: {provider.name}")
            payload = {
                "model": provider.model,
                "messages": [{"role": "user", "content": "hello"}],
                "temperature": 0.1,
                "max_tokens": 5,
            }
            await patched_client.chat.completions.create(**payload)
            await test_client.close()
            logger.info(f"服务商 '{provider.name}' 测试成功。")
            return True, "连接成功！"
        except OpenAIError as e:
            logger.error(f"测试服务商 '{provider.name}' 失败 (OpenAIError): {e}")
            return False, f"API错误: {e.body.get('message') if e.body else str(e)}"
        except Exception as e:
            logger.error(f"测试服务商 '{provider.name}' 时发生未知错误: {e}")
            return False, f"未知错误: {str(e)}"

    async def ai_greeting(self, job_detail):
        payload = {
            "model": self.active_provider.model,
            "messages": [
                {"role": "system", "content": self.greeting_prompt},
                {"role": "user", "content": f"目标职位关键要求：{job_detail}\n\n求职者真实简历：{self.resume_for_ai}"},
                {"role": "system", "content": "请生成符合上述要求的打招呼语，仅输出最终内容，不要用任何标记符号"}
            ],
            "temperature": self.active_provider.temperature,
        }
        try:
            response = await self.client.chat.completions.create(**payload)
            return response.choices[0].message.content.strip()
        except OpenAIError as e:
            logger.error(f"AI生成打招呼语失败: {e}")
            return None

    async def ai_hr_check(self, job_detail):
        messages = [
            {"role": "system", "content": self.ai_prompt},
            {"role": "user", "content": f"岗位要求：{job_detail}"},
            {"role": "user", "content": f"用户简历：{self.resume_for_ai}"},
            {"role": "user", "content": f"用户对工作岗位的要求：{self.job_requirements_prompt}"}
        ]
        try:
            response_obj = await self.client.chat.completions.create(
                model=self.active_provider.model,
                messages=messages,
                temperature=self.active_provider.temperature,
                response_model=AIAnalysisResult
            )
            match_conclusion = response_obj.match_conclusion
            raw_reasoning = response_obj.reasoning
            match = re.match(r"<think>(.*?)</think>(.*)", raw_reasoning, re.DOTALL)
            clean_reasoning = match.group(2).strip() if match else raw_reasoning
            return match_conclusion, clean_reasoning
        except OpenAIError as e:
            logger.error(f"AI分析失败: {e}")
            return False, f"AI分析异常: {e}"

    async def reload_config(self):
        """重新加载配置"""
        logger.info("AiAnalyzer 正在重新加载配置...")
        self._load_config()
        logger.info("AiAnalyzer 配置重载完成。")
        
    async def close(self):
        if hasattr(self, 'client') and self.client:
            # AsyncOpenAI 使用 close() 方法，不是 aclose()
            if hasattr(self.client, 'close'):
                await self.client.close()
            logger.info("AiAnalyzer 客户端会话已关闭")