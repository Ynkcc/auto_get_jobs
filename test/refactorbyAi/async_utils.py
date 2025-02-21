import aiohttp
import asyncio
import time

class TokenBucket:
    def __init__(self, rate=1, capacity=5):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.lastUpdate = time.time()

    async def getToken(self):
        while self.tokens < 1:
            await self.refill()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    async def refill(self):
        now = time.time()
        elapsed = now - self.lastUpdate
        self.tokens = min(self.capacity, self.tokens + int(elapsed * self.rate))
        self.lastUpdate = now

async def getJobInfo(securityId, lid, cookies, headers):
    url = f"https://www.zhipin.com/wapi/zpgeek/job/card.json?securityId={securityId}&lid={lid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, cookies=cookies, headers=headers, timeout=30) as response:
            return await response.json()

async def startChat(securityId, jobId, lid, cookies, headers):
    url = f"https://www.zhipin.com/wapi/zpgeek/friend/add.json?securityId={securityId}&jobId={jobId}&lid={lid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, cookies=cookies, headers=headers, timeout=30) as response:
            return await response.json()
