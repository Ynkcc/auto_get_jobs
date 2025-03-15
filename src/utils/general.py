# 标准库导入
import hashlib
import json
import logging
import os
import re
import threading
import time
from typing import List, Dict

# 第三方库导入
import asyncio
import aiohttp
import pandas as pd
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import mimetypes
import yaml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from .session_manager import SessionManager
import threading

# 本地模块导入
logger = logging.getLogger(__name__)

# 定义基础URL
BASE_URL = 'https://www.zhipin.com'


def save_jobs_to_csv(jobs: List[Dict], filename: str = 'jobs.csv') -> None:
    """
    将 jobs 数据导出为 CSV 文件
    :param jobs: 岗位数据列表，每个岗位是一个字典
    :param filename: 导出的文件名，默认为 jobs.csv
    """
    try:
        df = pd.DataFrame(jobs)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"数据已成功导出到 {filename}")
    except Exception as e:
        logger.error(f"导出 CSV 文件时发生错误：{e}")


class BrowserSessionHandler:
    def __init__(self, driver, login_data_file):
        self.driver = driver
        self.login_data_file = login_data_file
        self.save_thread = None
        self.stop_event = threading.Event()

    def load(self) -> bool:
        """加载登录数据"""
        try:
            with open(self.login_data_file, "r", encoding="utf-8") as f:
                login_data = json.load(f)

            self.driver.delete_all_cookies()
            for cookie in login_data["cookies"]:
                self.driver.add_cookie(cookie)

            self.driver.execute_script("window.localStorage.clear();")
            for k, v in login_data["localStorage"].items():
                self.driver.execute_script(f"localStorage.setItem('{k}', '{v}');")

            self.driver.execute_script("window.sessionStorage.clear();")
            for k, v in login_data["sessionStorage"].items():
                self.driver.execute_script(f"sessionStorage.setItem('{k}', '{v}');")

            logger.info("登录数据已加载")
            return True
        except FileNotFoundError:
            logger.warning("登录文件不存在")
            return False
        except Exception as e:
            logger.error(f"加载失败: {str(e)}")
            return False

    def save(self) -> bool:
        """保存登录数据"""
        try:
            directory = os.path.dirname(self.login_data_file)
            os.makedirs(directory, exist_ok=True)

            login_data = {
                "cookies": self.driver.get_cookies(),
                "localStorage": self.driver.execute_script("return Object.assign({}, localStorage);"),
                "sessionStorage": self.driver.execute_script("return Object.assign({}, sessionStorage);")
            }

            with open(self.login_data_file, "w", encoding="utf-8") as f:
                json.dump(login_data, f, indent=2, ensure_ascii=False)

            logger.info("登录数据已保存")
            return True
        except Exception as e:
            logger.error(f"保存失败: {str(e)}")
            return False

    def start_autosave(self, interval=60):
        """启动定时保存线程"""
        def saver_loop():
            while not self.stop_event.is_set():
                self.save()
                time.sleep(interval)

        if not self.save_thread or not self.save_thread.is_alive():
            self.stop_event.clear()
            self.save_thread = threading.Thread(target=saver_loop, daemon=True)
            self.save_thread.start()
            logger.info("自动保存已启动")

    def stop_autosave(self):
        """停止定时保存线程"""
        if self.save_thread and self.save_thread.is_alive():
            self.stop_event.set()
            self.save_thread.join(timeout=5)
            logger.info("自动保存已停止")

    def clear_data(self) -> bool:
        """清除浏览器数据"""
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            logger.info("浏览器数据已清空，可重新登录")
            return True
        except Exception as e:
            logger.error(f"清除数据失败: {str(e)}")
            return False


def init_driver(webdriver_config) -> webdriver:
    """
    初始化 WebDriver
    :param webdriver_config: WebDriver配置对象
    :return: WebDriver 实例
    """
    browser_type = webdriver_config.browser_type.lower()

    if browser_type == "edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService
        
        options = EdgeOptions()
        driver_path = webdriver_config.edge_driver_path
        ServiceClass = EdgeService
    else:  # 默认使用 Chrome
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        options = ChromeOptions()
        driver_path = webdriver_config.chrome_driver_path
        ServiceClass = ChromeService

    # 公共配置项
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('--log-level=3')  # 只记录严重错误

    # 浏览器特定配置
    log_prefs = {'performance': 'OFF'}
    if browser_type == "edge":
        options.set_capability('ms:loggingPrefs', log_prefs)
    else:
        options.set_capability('goog:loggingPrefs', log_prefs)

    # 无头模式配置
    if webdriver_config.headless:
        options.add_argument("--headless=new")
        options.add_argument("window-size=1920,1080")

    # 用户数据目录配置
    if webdriver_config.use_default_data_dir:
        data_dir = (
            os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
            if browser_type == "edge"
            else os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        )
        options.add_argument(f"user-data-dir={data_dir}")
        logger.info(f"{browser_type.capitalize()} 用户数据目录设置为: {data_dir}")

    # 初始化浏览器实例
    try:
        driver = (
            webdriver.Edge(service=ServiceClass(executable_path=driver_path), options=options)
            if browser_type == "edge"
            else webdriver.Chrome(service=ServiceClass(executable_path=driver_path), options=options)
        )
        return driver
    except Exception as e:
        logger.error(f"浏览器初始化失败: {str(e)}")
        raise

def build_search_url(job_search):
    """
    构造搜索URL
    """

    # 加载区域代码数据
    with open('config/search_params_config.json', 'r', encoding='utf-8') as f:
        params_data = json.load(f)

    location_dicts = {}
    city_code_map = params_data["cityCode"]

    # 处理区域配置
    if job_search.areas:
        # 处理明确指定的区域
        for city_name, districts in job_search.areas.items():
            if city_name not in city_code_map:
                logger.warning(f"未找到城市 [{city_name}] 的编码，已跳过")
                continue

            city_entry = city_code_map[city_name]
            city_code = list(city_entry.keys())[0]  # 获取城市编码

            valid_districts = [
                city_entry[city_code][district]
                for district in districts
                if district in city_entry[city_code]
            ]
            
            # 过滤无效区域
            invalid = set(districts) - set(city_entry[city_code].keys())
            if invalid:
                logger.warning(f"城市 [{city_name}] 下未找到区域: {', '.join(invalid)}")

            if valid_districts:
                location_dicts.setdefault(city_code, []).extend(valid_districts)
    else:
        # 处理城市全集
        for city_name in job_search.city:
            if city_name not in city_code_map:
                logger.warning(f"未找到城市 [{city_name}] 的编码，已跳过")
                continue

            city_entry = city_code_map[city_name]
            city_code = list(city_entry.keys())[0]
            location_dicts[city_code] = list(city_entry[city_code].values())

    # 参数验证
    if not location_dicts:
        raise ValueError("未找到有效的城市/区域配置")

    base_url = "https://www.zhipin.com/web/geek/job"

    # 转换到具体代码
    params_config = {
        'position': [str(params_data["position"][v]) for v in job_search.position],
        'industry': [str(params_data["industry"][v]) for v in job_search.industry],
        'experience': [str(params_data["experience"][v]) for v in job_search.experience],
        'salary': [str(params_data["salary"][v]) for v in job_search.salary],
        'jobType': [str(params_data["jobType"][v]) for v in job_search.jobType],
        'scale': [str(params_data["scale"][v]) for v in job_search.scale],
        'stage': [str(params_data["stage"][v]) for v in job_search.stage],
        'query': job_search.query  # 直接使用列表
    }

    # 过滤空参数
    params_config = {k: v for k, v in params_config.items() if v}

    # 生成参数组合
    for city_code, districts in location_dicts.items():
        for district in districts:
            base_params = {'city': city_code, 'areaBusiness': district}
            
            if not params_config:
                yield f"{base_url}?city={city_code}&areaBusiness={district}"
                continue

            # 递归生成参数组合
            def generate_params(keys: List[str], values: List[List[str]], index: int = 0, current: dict = None):
                current = current.copy() if current else base_params.copy()
                if index == len(keys):
                    param_str = '&'.join(f"{k}={v}" for k, v in sorted(current.items()))
                    yield f"{base_url}?{param_str}"
                else:
                    for value in values[index]:
                        current[keys[index]] = value
                        yield from generate_params(keys, values, index + 1, current)

            yield from generate_params(
                keys=list(params_config.keys()),
                values=list(params_config.values())
            )

def get_page_jobs_info(driver):
    jobs = []
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, "html.parser")
    # 找到所有的岗位信息块
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


def next_page(driver):
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


def filter_jobs_by_salary(jobs: List[Dict], expected_salary: float) -> List[Dict]:
    """
    根据期望薪资过滤岗位
    :param jobs: 岗位列表
    :param expected_salary: 期望薪资（单位：K）
    :return: 符合条件的岗位列表
    """
    jobs_matching_salary = []
    for job in jobs:
        job_name = job['job_name']
        job_salary = job['job_salary']

        # 使用正则表达式去除类似 "·13薪" 的后缀
        job_salary = re.sub(r'·\d+薪', '', job_salary)

        # 解析薪资范围
        if '元/天' in job_salary:
            daily_salary = job_salary.replace('元/天', '')
            daily_salary_range = daily_salary.split('-')
            min_daily_salary = int(daily_salary_range[0])
            max_daily_salary = int(daily_salary_range[1]) if len(daily_salary_range) > 1 else min_daily_salary
            min_monthly_salary = min_daily_salary * 22 / 1000  # 转换为 K
            max_monthly_salary = max_daily_salary * 22 / 1000  # 转换为 K
        elif "k" in job_salary or "K" in job_salary:
            salary_range = job_salary.replace('K', '').replace('k', '').split('-')
            min_monthly_salary = float(salary_range[0])
            max_monthly_salary = float(salary_range[1]) if len(salary_range) > 1 else min_monthly_salary
        else:
            logger.warning(f"薪资格式错误 招聘岗位: {job_name} | {job_salary}")
            continue

        # 判断薪资是否满足条件
        if min_monthly_salary >= expected_salary:
            jobs_matching_salary.append(job)
        else:
            logger.info(f"薪资太低 招聘岗位: {job_name} | {job_salary}")
    return jobs_matching_salary


def parse_params(link):
    """
    从招聘链接中提取关键参数
    """
    pattern = r'/job_detail/([^.]+)\.html\?lid=([^&]+)&securityId=([^&]+)'
    match = re.search(pattern, link)
    return match.groups() if match else None


def get_user_info():
    url = "https://www.zhipin.com/wapi/zpuser/wap/getUserInfo.json"
    session = SessionManager.get_sync_session()
    try:
        user_info = session.get(url).json()
        user_id = user_info['zpData']['userId']
        user_name = user_info['zpData']['name']
        true_man = user_info['zpData']['trueMan']
        print(f"成功获取到用户信息: 用户名是：{user_name},账号id是：{user_id}")
        if not true_man:
            print("警告：本账号已被BOSS直聘标记")
    except Exception as e:
        print("获取用户信息失败")
        print(e)
        return "UNKNOWN", None
    return user_id, user_info

def get_wt2():
    """获取wt2验证参数"""
    try:
        url = "https://www.zhipin.com/wapi/zppassport/get/wt"
        session = SessionManager.get_sync_session()
        response = session.get(url, timeout=10)
        response.raise_for_status()
        wt2_data = response.json()

        if wt2_data['code'] == 0:
            return wt2_data['zpData'].get('wt2')
        raise Exception(f"获取wt2失败: {wt2_data.get('message')}")
    except Exception as e:
        logger.error(f"获取wt2异常: {str(e)}")
        return None


def calculate_md5(file_path):
    """计算文件的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def full_upload_image(file_path,securityId):
    """
    上传图片
    """
    try:
        url = "https://www.zhipin.com/wapi/zpupload/image/uploadSingle"
        session = SessionManager.get_sync_session()
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            mp_encoder = MultipartEncoder(
                fields=[
                    ('securityId', securityId),
                    ('source', 'chat_file'),
                    ('file', (os.path.basename(file_path), f, mime_type ))
                ]
            )
            headers = {'Content-Type': mp_encoder.content_type,
            'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            }
            response = session.post(url, data=mp_encoder,headers=headers)
        zp_data = response.json()["zpData"]
        origin_width = zp_data["metadata"]["width"]
        origin_height = zp_data["metadata"]['height']
        tiny_width = 200
        tiny_height = int(tiny_width * origin_height / origin_width)
        result = {
            "tinyImage": {
                "url": zp_data['tinyUrl'],
                "width": tiny_width,
                "height": tiny_height
            },
            "originImage": {
                "url": zp_data['url'],
                "width": origin_width,
                "height": origin_height
            }
        }
        return result
    except Exception:
        logger.exception(f"上传简历图片出现错误")
        return None

def quickly_upload_image(file_md5, securityId):
    # 快速上传接口（若服务端已有相同文件则直接返回结果）
    url = "https://www.zhipin.com/wapi/zpupload/quicklyUpload"
    data = {
        "fileMd5": file_md5,  # use file_md5 instead of calculate_md5(file_path)
        "fileSize": 0,  # remove os.path.getsize(file_path),
        "source": "chat_file",
        "securityId": securityId
    }
    session = SessionManager.get_sync_session()
    response = session.post(url, data=data)
    zp_data = response.json()["zpData"]
    if zp_data.get("url"):
        origin_width = zp_data["metadata"]["width"]
        origin_height = zp_data["metadata"]['height']
        tiny_width = 200
        tiny_height = int(tiny_width * origin_height / origin_width)
        result = {
            "tinyImage": {
                "url": zp_data['tinyUrl'],
                "width": tiny_width,
                "height": tiny_height
            },
            "originImage": {
                "url": zp_data['url'],
                "width": origin_width,
                "height": origin_height
            }
        }
    else:
        result = False
    return result


def upload_image(file_path, securityId, resume_image_md5=None): 
    quickly_upload_result = quickly_upload_image(resume_image_md5, securityId)
    if quickly_upload_result:
        return quickly_upload_result
    else:
        full_upload_result =  full_upload_image(file_path, securityId) 
        return full_upload_result
    



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

async def get_job_info(securityId, lid, max_retries=3):
    path = "/wapi/zpgeek/job/card.json"
    url = f"{BASE_URL}{path}"
    params = {
        "securityId": securityId,
        "lid": lid
    }

    async def _request(attempt):
        try:
            session = await SessionManager.get_async_session()
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30 + attempt*5)  # 动态超时
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    logger.warning(f"[403 Forbidden] 可能触发反爬虫 securityId={securityId}")
                    return None
                else:
                    logger.error(f"请求失败 HTTP {response.status} - {await response.text()}")
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"请求异常 [{type(e).__name__}] 第{attempt}次重试: {str(e)}")
            return None

    # 重试逻辑
    for attempt in range(1, max_retries + 1):
        result = await _request(attempt)
        if result is not None:
            return result
        await asyncio.sleep(min(2 ** attempt, 10))  # 指数退避

    logger.error(f"请求失败（已达最大重试次数 {max_retries}）")
    return None

async def start_chat(securityId, jobId, lid):
    path = "/wapi/zpgeek/friend/add.json"
    url = f"{BASE_URL}{path}"
    params = {
        "securityId": securityId,
        "jobId": jobId,
        "lid": lid
    }

    session = await SessionManager.get_async_session()
    async with session.get(url, params=params, timeout=30) as response:
        if response.status == 200:
            return await response.json()
        else:
            response.raise_for_status()


# 以下接口待验证
async def get_boss_list(page: int, cookies=None, headers=None):
    path = "/wapi/zprelation/friend/getGeekFriendList.json"
    url = f"https://www.zhipin.com{path}"
    params = {"page": page}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
            return await response.json()


async def get_boss_data(encryptBossId: str, securityId: str, source_type="0", cookies=None, headers=None):
    path = "/wapi/zpgeek/chat/bossdata.json"
    url = f"https://www.zhipin.com{path}"
    params = {
        "bossId": encryptBossId,
        "bossSource": source_type,
        "securityId": securityId
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
            return await response.json()


async def get_history_msg(encryptBossId: str, securityId: str, cookies=None, headers=None):
    path = "/wapi/zpchat/geek/historyMsg"
    url = f"https://www.zhipin.com{path}"
    params = {
        "bossId": encryptBossId,
        "groupId": encryptBossId,
        "securityId": securityId,
        "maxMsgId": "0",
        "c": "20",
        "page": "1"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
            return await response.json()


async def request_send_resume(bossId: str, resumeId: str, cookies=None, headers=None):
    path = "/geek/new/requestSendResume.json"
    url = f"https://www.zhipin.com{path}"
    params = {
        "bossId": bossId,
        "resumeId": resumeId,
        "toSource": "0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, cookies=cookies, headers=headers) as response:
            return await response.json()


async def get_resumes(cookies=None, headers=None):
    path = "/wapi/zpgeek/resume/attachment/checkbox.json"
    url = f"https://www.zhipin.com{path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, cookies=cookies, headers=headers) as response:
            return await response.json()
