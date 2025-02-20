import asyncio
import time
import random

class RateLimiter:
    def __init__(self, rate_limit: int, per_seconds: int):
        # rate_limit 是每秒最多请求的次数，per_seconds 是时间窗口大小（秒）
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.tokens = rate_limit
        self.last_checked = time.time()

    async def wait_for_token(self):
        while True:
            current_time = time.time()
            elapsed_time = current_time - self.last_checked

            if elapsed_time >= self.per_seconds:
                # 超过了时间窗口，重置令牌
                self.tokens = self.rate_limit
                self.last_checked = current_time

            if self.tokens > 0:
                self.tokens -= 1
                return  # 获取到令牌，继续执行
            else:
                # 如果没有令牌，等待
                await asyncio.sleep(0.1)

# 模拟从网页1爬取数据
async def fetch_data_from_page1(keyword: str, start_time):

    # 模拟请求和处理的时间
    await asyncio.sleep(2)  # 模拟从网页1获取数据的耗时
    elapsed_time = time.time() - start_time
    print(f"从网页1查询关键词 '{keyword}' 完成，耗时 {elapsed_time:.2f}秒")
    return f"数据 for {keyword}"

# 模拟AI处理，模拟一个非常耗时的操作
async def send_to_ai(data: str, start_time):
    # 模拟AI请求和处理的耗时
    await asyncio.sleep(random.randint(1, 30))  # 模拟AI处理，耗时随机，1到30秒之间
    elapsed_time = time.time() - start_time
    print(f"AI处理数据 '{data}' 完成，耗时 {elapsed_time:.2f}秒")
    return f"AI结果 for {data}"

# 模拟发送数据到网页2
async def send_to_page2(result: str, start_time):

    # 模拟发送到网页2的耗时
    await asyncio.sleep(1)  # 模拟发送到网页2的耗时
    elapsed_time = time.time() - start_time
    print(f"将结果 '{result}' 发送到网页2，耗时 {elapsed_time:.2f}秒")

# 控制访问速率
async def process_keyword(keyword: str, rate_limiter: RateLimiter, start_time: float):
    await rate_limiter.wait_for_token()  # 控制请求速率
    data = await fetch_data_from_page1(keyword, start_time)
    
    # 直接并发执行 send_to_ai，减少等待时间
    ai_result_task = asyncio.create_task(send_to_ai(data, start_time))
    
    await rate_limiter.wait_for_token()  # 控制请求速率
    await send_to_page2(await ai_result_task, start_time)

# 主函数，处理多个关键词
async def main():
    start_time = time.time()  # 记录程序开始运行的时间
    keywords = [str(i) for i in range(101)]  # 0-100的关键词列表
    
    # 创建一个令牌桶，限制每秒最多3个请求
    rate_limiter = RateLimiter(rate_limit=1, per_seconds=1)
    
    # 逐个处理关键词，控制网页1和网页2的访问速率
    tasks = []
    for keyword in keywords:
        tasks.append(process_keyword(keyword, rate_limiter, start_time))
    
    # 执行所有任务并等待完成
    await asyncio.gather(*tasks)

# 运行协程
asyncio.run(main())
