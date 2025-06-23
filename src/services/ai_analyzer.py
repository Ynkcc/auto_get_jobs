# src/services/ai_analyzer.py
import logging
import re
from openai import AsyncOpenAI, AsyncAzureOpenAI, OpenAIError
from pydantic import BaseModel
import instructor  # 导入 instructor

from ..common.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 定义用于结构化输出的 Pydantic 模型
# instructor 会确保AI的输出严格遵循此结构
class AIAnalysisResult(BaseModel):
    match_conclusion: bool
    reasoning: str


class AiAnalyzer:
    def __init__(self):
        """
        初始化 AiAnalyzer，加载配置并设置AI客户端。
        使用 instructor 来增强(patch)原始的 OpenAI 客户端，以便可靠地进行结构化输出。
        """
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
        
        # 使用 instructor 来增强 client
        base_client = self._initialize_client(config_ai)
        # --- 修改点 ---
        # 由于模型不支持 'TOOLS' 模式，我们切换到更兼容的 'JSON' 模式
        self.client = instructor.patch(base_client, mode=instructor.Mode.JSON)

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
        """从文件加载用于AI分析的简历内容"""
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
        """
        使用AI分析职位是否匹配，并通过 instructor 返回结构化结果。
        """
        messages = [
            {"role": "system", "content": self.ai_prompt},
            {"role": "user", "content": f"岗位要求：{job_detail}"},
            {"role": "user", "content": f"用户简历：{self.resume_for_ai}"},
            {"role": "user", "content": f"用户对工作岗位的要求：{self.job_requirements_prompt}"}
        ]
        try:
            # 在 JSON 模式下，instructor 同样会自动处理 response_model
            response_obj = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_model=AIAnalysisResult
            )

            # 直接从返回的Pydantic对象中获取数据
            match_conclusion = response_obj.match_conclusion
            raw_reasoning = response_obj.reasoning
            
            # 按要求保留对 <think> 标签的过滤逻辑
            match = re.match(r"<think>(.*?)</think>(.*)", raw_reasoning, re.DOTALL)
            clean_reasoning = match.group(2).strip() if match else raw_reasoning
            
            return match_conclusion, clean_reasoning

        except OpenAIError as e:
            logger.error(f"AI分析失败: {e}")
            return False, f"AI分析异常: {e}"

    async def close(self):
        """关闭AI客户端会话以释放资源。"""
        if self.client:
            # instructor 增强过的 client 同样支持 aclose
            await self.client.close()
            logger.info("AiAnalyzer 客户端会话已关闭")