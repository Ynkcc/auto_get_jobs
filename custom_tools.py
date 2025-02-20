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



# 保存登录数据的文件名
LOGIN_DATA_FILE = "login_data.json"

def save_jobs_to_csv(jobs, filename='jobs.csv'):
    """
    将 jobs 数据导出为 CSV 文件
    jobs: 岗位数据列表，每个岗位是一个字典
    filename: 导出的文件名，默认为 jobs.csv
    """
    try:
        # 将 jobs 转换为 DataFrame
        df = pd.DataFrame(jobs)
        # 导出为 CSV 文件
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"数据已成功导出到 {filename}")
    except Exception as e:
        print(f"导出 CSV 文件时发生错误：{e}")



def save_login_data(driver):
    """
    保存登录数据（cookies、localStorage、sessionStorage）
    """
    login_data = {
        "cookies": driver.get_cookies(),
        "localStorage": driver.execute_script("return Object.assign({}, window.localStorage);"),
        "sessionStorage": driver.execute_script("return Object.assign({}, window.sessionStorage);")
    }
    with open(LOGIN_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(login_data, f, ensure_ascii=False, indent=4)
    print("登录数据已保存。")

def load_login_data(driver):
    """
    加载登录数据（cookies、localStorage、sessionStorage）
    """
    try:
        with open(LOGIN_DATA_FILE, "r", encoding="utf-8") as f:
            login_data = json.load(f)
        
        # 加载 cookies
        for cookie in login_data["cookies"]:
            driver.add_cookie(cookie)
        
        # 加载 localStorage
        for key, value in login_data["localStorage"].items():
            driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
        
        # 加载 sessionStorage
        for key, value in login_data["sessionStorage"].items():
            driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")
        
        print("登录数据已加载。")
        return True
    except FileNotFoundError:
        print("未找到登录数据文件，需要重新登录。")
        return False
    except Exception as e:
        print(f"加载登录数据时发生错误: {e}")
        return False

# 初始化 WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 防止被检测为自动化工具
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.set_capability('goog:loggingPrefs', {'performance': 'OFF'})  # 关闭性能日志
    options.add_argument('--log-level=3')  # 只记录严重错误
    driver_path = os.path.join("chromedriver", "chromedriver.exe")
    driver = webdriver.Chrome(service=Service(driver_path),options=options)

    return driver

def wait_for_redirect(driver, timeout=60):
    """
    等待页面跳转到指定 URL
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.current_url == "https://www.zhipin.com/web/geek/job-recommend" or
                      d.current_url == "https://www.zhipin.com"
        )
        print("页面跳转成功。")
    except Exception as e:
        print(f"页面跳转失败: {e}")



# 封装线程启动的函数
def start_cookie_saver(driver, interval=60):
    # 定时保存 cookies 的线程函数
    def save_cookies_periodically(driver, interval=60):
        while True:
            save_login_data(driver)  # 调用保存 cookies 的函数
            time.sleep(interval)  # 间隔时间（单位：秒）
    # 创建并启动一个线程来定期保存 cookies
    save_thread = threading.Thread(target=save_cookies_periodically, args=(driver, interval))
    save_thread.daemon = True  # 设置为守护线程，确保主程序退出时线程也会退出
    save_thread.start()
    print("定时保存 cookies 的线程已启动")

def get_cityid(city):
    """
    获取城市的ID
    """
    cityid_dict = json.load(open("city_list.json", "r", encoding="utf-8"))
    cityid = cityid_dict[city]
    
    return cityid

def buildSearchUrl(query, city, degree = None):
    """
    构造搜索URL
    :param query: 职位
    :param city: 城市
    """
    cityid = get_cityid(city)
    searchUrl = f"https://www.zhipin.com/web/geek/job?query={query}&city={cityid}"
    if degree:
        searchUrl += f"&degree={degree}"
    return searchUrl

def getPageJobsInfo(driver):
    jobs=[]
    html_content = driver.page_source 
    soup = BeautifulSoup(html_content, "html.parser")
    #找到所有的岗位信息块
    job_cards = soup.find_all('li', class_='job-card-wrapper')
    # print(job_cards)
    
    for job_card in job_cards:
        job_name = job_card.find('span', class_="job-name").text.strip()
        job_salary = job_card.find('span', class_="salary").text.strip()
        job_link = job_card.find('a', class_='job-card-left')['href']
        # 公司名称
        company_name = job_card.find('h3', class_='company-name').text.strip()
        # 公司标签列表
        company_tag_list = job_card.find('ul', class_='company-tag-list')
        company_tags = [tag.text.strip() for tag in company_tag_list.find_all('li')] if company_tag_list else []
        # 将提取的信息添加到 jobs 列表中
        jobs.append({
            'job_name': job_name,
            'job_salary': job_salary,
            'job_link': job_link,
            'company_name': company_name,
            'company_tags': company_tags
        })
        
    # 打印当前岗位数量（可选）
    # print(f"当前岗位数量：{len(jobs)}")
    return jobs

def nextPage(driver):
    try:
        next_page_button = driver.find_element(By.CLASS_NAME, "ui-icon-arrow-right")
        print("开始采集下一页")
        if "disabled" in next_page_button.find_element(By.XPATH, "..").get_attribute("class"):
            print("没有下一页了，退出循环。")
            return False
        driver.execute_script("arguments[0].click();", next_page_button)
        return True
    except Exception:
        print("可能找不到下一页，退出循环。")
        return False

def filterJobsBySalary(jobs,expectedSalary):
    jobsMatchingSalary=[]
    for job in jobs:
        job_name = job['job_name']
        job_salary = job['job_salary']

        # 使用正则表达式去除类似 "·13薪" 的后缀
        job_salary = re.sub(r'·\d+薪', '', job_salary)

        # 解析薪资范围
        if '元/天' in job_salary:
            # 处理日薪情况，按每月22天计算月薪
            daily_salary = job_salary.replace('元/天', '')
            daily_salary_range = daily_salary.split('-')
            min_daily_salary = int(daily_salary_range[0])
            max_daily_salary = int(daily_salary_range[1]) if len(daily_salary_range) > 1 else min_daily_salary
            min_monthly_salary = min_daily_salary * 22 / 1000  # 转换为K
            max_monthly_salary = max_daily_salary * 22 / 1000  # 转换为K
        elif "k" in job_salary or "K" in job_salary:
            # 处理月薪情况
            salary_range = job_salary.replace('K', '').replace('k', '').split('-')
            min_monthly_salary = float(salary_range[0])
            max_monthly_salary = float(salary_range[1]) if len(salary_range) > 1 else min_monthly_salary
        else:
            #格式不对，直接放弃
            print(f"薪资格式错误：招聘岗位: {job_name} | {job_salary}")
            continue
        # 判断薪资是否满足条件
        if min_monthly_salary >= expectedSalary:
            jobsMatchingSalary.append(job)
    return jobsMatchingSalary   


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

async def getJobinfo(securityId, lid, cookies=None, headers=None):
    path = "/wapi/zpgeek/job/card.json"
    url = f"{base_url}{path}"
    params = {
        "securityId": securityId,
        "lid": lid
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
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
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()

async def send_to_ai(client,job_detail):
    """调用AI模型进行岗位匹配判断"""
    for _ in range(5): #失败后，多次重试
        try:
            # 构建系统提示（与part1保持相似的逻辑但不复用函数）
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
            
            # 调用Azure客户端
            response = await client.complete(
                messages=messages,
                max_tokens=50,
                temperature=0.1,
                stream=False
            )
            
            # 严格解析响应内容
            return "true" in response.choices[0].message.content.lower()
        except Exception as e:
            print(f"AI分析失败: {e}")
            return False

class JobProcessor:
    def __init__(self, comm_queue: Queue, done_event):
        self.comm_queue = comm_queue
        self.done_event = done_event
        self.rate_limit = TokenBucket(rate=0.2, capacity=3)  # 限速设置，每秒最多3次请求
        self.loop = None
        self.client=init_ChatClient()
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
            job_detail = await getJobinfo(security_id, lid, cookies, headers)

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
            print(job_requirements)
            # 准备AI分析参数
            analysis_data = {
                "job_requirements": job_requirements,
                "user_requirements": self.user_requirements
            }

            # 不限速调用
            ai_result = await send_to_ai(self.client,analysis_data)
            

            if ai_result:
                # 限速调用
                await self.rate_limit.get_token()  # 限速调用
                result = await startChat(security_id, job_id, lid, cookies, headers)
                print(f"job {job_data['job_name']}: {result['message']}")
            else:
                print(f"job {job_data['job_name']}: ai认为不匹配")
            return True
    
        except Exception as e:
            print(f"Error processing job {job_data['job_name']},{job_id}:\n {e}")
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