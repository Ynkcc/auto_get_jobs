from async_utils import TokenBucket, getJobInfo, startChat
from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import asyncio
import re
import os

class JobProcessor:
    def __init__(self, commQueue, doneEvent):
        self.commQueue = commQueue
        self.doneEvent = doneEvent
        self.rateLimiter = TokenBucket(rate=1, capacity=5)
        self.client = self.initChatClient()
        self.userRequirements = self.loadUserRequirements()
        self.semaphore = asyncio.Semaphore(5)

    def initChatClient(self):
        endpoint = os.getenv("AZUREAI_ENDPOINT_URL").strip()
        key = os.getenv("AZUREAI_ENDPOINT_KEY").strip()
        return ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
            model=os.getenv("MODEL").strip(),
            temperature=0.2
        )

    def loadUserRequirements(self):
        try:
            with open('user_requirements.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    async def processJob(self, job, cookies, headers):
        async with self.semaphore:
            await self.rateLimiter.getToken()
            
            match = re.search(r'/job_detail/([^.]+)\.html\?lid=([^&]+)&securityId=([^&]+)', job['job_link'])
            if not match:
                return False

            try:
                jobDetail = await getJobInfo(match.group(3), match.group(2), cookies, headers)
                if not self.checkHrActive(jobDetail):
                    return False

                if await self.aiMatch(jobDetail):
                    await startChat(match.group(3), match.group(1), match.group(2), cookies, headers)
                    return True
                return False
            except Exception as e:
                print(f"Job processing failed: {e}")
                return False

    def checkHrActive(self, jobDetail):
        inactiveStatus = ["本月活跃", "2月内活跃", "3月内活跃", "半年前活跃"]
        status = jobDetail['zpData']['jobCard'].get('activeTimeDesc', '')
        return status not in inactiveStatus

    async def aiMatch(self, jobDetail):
        prompt = """# Role: HR Specialist
        Analyze if the candidate meets 50%+ job requirements.
        Return ONLY 'true' or 'false'."""
        
        jobDesc = f"""
        Position: {jobDetail['zpData']['jobCard']['jobName']}
        Requirements: {jobDetail['zpData']['jobCard']['postDescription']}
        Experience: {jobDetail['zpData']['jobCard']['experienceName']}
        Education: {jobDetail['zpData']['jobCard']['degreeName']}
        """
        
        response = await self.client.complete(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Job: {jobDesc}\nCandidate: {self.userRequirements}"}
            ],
            max_tokens=10
        )
        
        return "true" in response.choices[0].message.content.lower()

    def startProcessing(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while True:
                batch = self.commQueue.get()
                if batch is None:
                    break
                    
                tasks = [self.processJob(job, batch['cookies'], batch['headers']) 
                        for job in batch['jobs']]
                        
                results = loop.run_until_complete(asyncio.gather(*tasks))
                print(f"Processed batch with {sum(results)} successes")
                self.doneEvent.set()
                
        finally:
            loop.run_until_complete(self.client.close())
            loop.close()
