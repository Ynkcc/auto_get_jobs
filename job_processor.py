from multiprocessing import Queue
from utils import *
import pandas as pd
import json
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
from bs4 import BeautifulSoup
import re
import asyncio
import random
from multiprocessing import Process, Queue, Event
import aiohttp
from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from async_utils import *

class JobProcessor:
    def __init__(self, comm_queue: Queue, done_event):
        self.comm_queue = comm_queue
        self.done_event = done_event
        self.rate_limit = TokenBucket(rate=0.2, capacity=3)  # 限速设置，每秒最多3次请求
        self.loop = None
        self.user_requirements = self._load_user_requirements()
        self.inactive_keywords = ["本月活跃", "2月内活跃", "3月内活跃", 
                                "4月内活跃", "5月内活跃", "半年前活跃", "近半年活跃"]

    def _load_user_requirements(self):
        """从文件加载用户简历"""
        try:
            with open('user_requirements.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print("警告：未找到user_requirements.md文件")
            return ""

    async def _process_single_job(self, job_data, cookies, headers):
        # 解析job_link中的参数
        link = job_data['job_link']
        match = re.search(r'/job_detail/([^.]+)\.html\?lid=([^&]+)&securityId=([^&]+)', link)
        if not match:
            return False
            
        job_id, lid, security_id = match.groups()
        
        # 实际的请求处理逻辑
        try:

            # 获取职位详细信息（限速）
            await self.rate_limit.get_token()  # 限速调用
            job_detail = await getJobInfo(security_id, lid, cookies, headers)

            # 检查HR活跃状态
            active_status = job_detail['zpData']['jobCard'].get('activeTimeDesc', '')
            if active_status in self.inactive_keywords:
                print(f"跳过{job_data['job_name']}：HR活跃状态[{active_status}]不符合要求")
                return False

            # 构建岗位要求
            card = job_detail['zpData']['jobCard']
            job_requirements = (
                f"职位名称：{card['jobName']}\n"
                f"岗位职责：{card['postDescription']}\n"
                f"经验要求：{card['experienceName']}\n"
                f"学历要求：{card['degreeName']}"
            )

            # 准备AI分析参数
            analysis_data = {
                "job_requirements": job_requirements,
                "user_requirements": self.user_requirements
            }

            # 不限速调用
            ai_result = await aiHrCheck(analysis_data)
            

            if ai_result:
                # 限速调用
                await self.rate_limit.get_token()  # 限速调用
                result = await startChat(security_id, job_id, lid, cookies, headers)
                print(f"job {job_data['job_name']}: {result['message']}\n{job_requirements}\n\n")

            else:
                print(f"job {job_data['job_name']}: ai认为不匹配\n{job_requirements}\n\n")
            return True
    
        except Exception as e:
            print(f"Error processing job {job_data['job_name']},{job_id}:\n {str(e)}")
            return False

    async def _process_batch(self, jobs_batch, cookies, headers):
        tasks = [self._process_single_job(job, cookies, headers) for job in jobs_batch]
        return await asyncio.gather(*tasks)

    def start_processing(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        while True:
            batch = self.comm_queue.get()
            if batch is None:  # 终止信号
                self.done_event.set()
                break
                
            # 提取 cookies 和 headers
            cookies = batch.get("cookies")
            headers = batch.get("headers")
            jobs_batch = batch.get("jobs")

            results = self.loop.run_until_complete(self._process_batch(jobs_batch, cookies, headers))
            print(f"Processed batch with {len(results)} jobs")
            self.done_event.set()  # 通知主进程处理完成
