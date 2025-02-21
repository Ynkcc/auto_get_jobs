import os
import aiohttp
from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import time
import asyncio

def init_ChatClient():
    # 配置 Azure API 端点和密钥
    endpoint = os.getenv("AZUREAI_ENDPOINT_URL").strip()
    key = os.getenv("AZUREAI_ENDPOINT_KEY").strip()
    model = os.getenv("MODEL").strip()

    # 创建 Azure 客户端
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
        model=model,
        temperature=0.2
    )
    return client
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

async def aiHrCheck(job_detail):
    for attempt in range(5):  # 带清晰命名的重试计数器
        client = None
        try:
            client = init_ChatClient()
            # 构建消息（保持原始逻辑）
            hr_prompt = """# Role: 资深HR专家
## 目标：
1. 分析岗位需求与候选人简历的匹配度
2. 输出严格遵循以下规则：
- 只返回"true"或"false"
- 匹配度阈值设为0.5
"""
            messages = [
                {"role": "system", "content": hr_prompt},
                {"role": "user", "content": f"岗位要求：{job_detail['job_requirements']}\n\n候选人简历：{job_detail['user_requirements']}"}
            ]
            
            # 调用API
            response = await client.complete(
                messages=messages,
                max_tokens=50,
                temperature=0.1,
                stream=False
            )
            
            # 解析响应
            content = response.choices[0].message.content.lower()
            return "true" in content
            
        except aiohttp.ClientError as e:
            print(f"网络请求失败 ({attempt+1}/5): {str(e)}")
            await asyncio.sleep(2 ** attempt)  # 指数退避
        except KeyError as e:
            print(f"响应格式错误: {str(e)}")
            break  # 无需重试的结构性错误
        except Exception as e:
            print(f"AI分析失败 ({attempt+1}/5): {str(e)}")
            await asyncio.sleep(1)
        finally:
            # 确保每次尝试后关闭客户端
            if client is not None:
                await client.close()
                await asyncio.sleep(0.1)  # 给关闭操作留出时间
    
    return False  # 所有重试失败
