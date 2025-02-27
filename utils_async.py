import os
import aiohttp
from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import time
import asyncio
import re

class AIAnalyzer():
    def __init__(self,config_ai):
        self.api_url = config_ai['api_url']
        self.api_key = config_ai['api_key']
        self.model = config_ai['model']
        self.temperature=config_ai["temperature"]
        self.provider = config_ai['provider']
        self.resumeFileName = config_ai["resume_for_ai_file"]
        self.resume_for_ai=self._load_user_requirements()
        self.ai_prompt=config_ai["prompt"]
        self.headers=self._get_provider_handlers()

    def _load_user_requirements(self):
        """从文件加载用户简历"""
        try:
            with open(self.resumeFileName, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"警告：未找到用于ai分析的简历文件{self.resumeFileName}")
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



    async def aiHrCheck(self, job_detail):
        for attempt in range(5):
            try:
                async with aiohttp.ClientSession() as session:

                    # 构建请求体
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.ai_prompt},
                            {"role": "user", "content": f"岗位要求：{job_detail}\
                                \n用户简历/要求：{self.resume_for_ai}"}
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
                        match = re.match(r"<think>(.*?)</think>(.*)", origin_content, re.DOTALL)
                        if match:
                            # print("\tThinking:", match.group(1))
                            # print("\tAnswer:", match.group(2))
                            content= match.group(2)
                        else:
                            content=origin_content
                        return "true" in content

            except aiohttp.ClientError as e:
                print(f"网络请求失败 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(2 ** attempt)
            except KeyError as e:
                print(f"响应格式错误: {str(e)}")
                break
            except TimeoutError as e:
                print(f"连接超时 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(2 ** attempt)
            #部分平台的ai响应存在截断，导致响应体不能被解析成json
            except Exception as e:
                print(f"AI分析失败 ({attempt+1}/5): {str(e)}")
                await asyncio.sleep(1)
        
        return False

class TokenBucket:
    def __init__(self, rate: int, capacity: int):
        self.rate = rate  # 每秒生成的令牌数
        self.capacity = capacity  # 桶的容量
        self.tokens = capacity  # 初始化令牌数为桶容量
        self.last_check = time.time()

    async def get_token(self):
        while True:
            now = time.time()
            elapsed = now - self.last_check
            if elapsed > 1:
                # 每秒重新生成令牌
                self.tokens = min(self.capacity, self.tokens + int(elapsed * self.rate))
                self.last_check = now
            if self.tokens > 0:
                self.tokens -= 1
                break
            else:
                # 等待直到有令牌
                await asyncio.sleep(1 / self.rate)

base_url = "https://www.zhipin.com"

async def getJobInfo(securityId, lid, cookies=None, headers=None):
    path = "/wapi/zpgeek/job/card.json"
    url = f"{base_url}{path}"
    params = {
        "securityId": securityId,
        "lid": lid
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()

async def startChat(securityId, jobId, lid, cookies=None, headers=None):
    path = "/wapi/zpgeek/friend/add.json"
    url = f"{base_url}{path}"
    params = {
        "securityId": securityId,
        "jobId": jobId,
        "lid": lid
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()
