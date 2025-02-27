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
import requests
import yaml



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

class SessionManager:
    def __init__(self, driver, login_data_file):
        self.driver = driver
        self.login_data_file = login_data_file
        self.save_thread = None
        self.stop_event = threading.Event()  # 停止事件标志

    def load(self):
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
            
            print("登录数据已加载")
            return True
        except FileNotFoundError:
            print("登录文件不存在")
            return False
        except Exception as e:
            print(f"加载失败: {str(e)}")
            return False

    def save(self):
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
            
            print("登录数据已保存")
            return True
        except Exception as e:
            print(f"保存失败: {str(e)}")
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
            print("自动保存已启动")

    def stop_autosave(self):
        """停止定时保存线程"""
        if self.save_thread and self.save_thread.is_alive():
            self.stop_event.set()
            self.save_thread.join(timeout=5)
            print("自动保存已停止")

    def clear_data(self):
        """清除浏览器数据"""
        try:
            # 清除 cookies
            self.driver.delete_all_cookies()
            
            # 清除 localStorage
            self.driver.execute_script("window.localStorage.clear();")
            
            # 清除 sessionStorage
            self.driver.execute_script("window.sessionStorage.clear();")
            
            print("浏览器数据已清空，可重新登录")
            return True
        except Exception as e:
            print(f"清除数据失败: {str(e)}")
            return False

# 初始化 WebDriver
def init_driver(webdriverConfig):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 防止被检测为自动化工具
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.set_capability('goog:loggingPrefs', {'performance': 'OFF'})  # 关闭性能日志
    options.add_argument('--log-level=3')  # 只记录严重错误
    if webdriverConfig.get("headless", False):
        #无头模式访问
        options.add_argument("--headless")
        options.add_argument("window-size=1920,1080")
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



def get_cityid(city):
    """
    获取城市的ID
    """
    cityid_dict = json.load(open("city_list.json", "r", encoding="utf-8"))
    cityid = cityid_dict[city]
    
    return cityid

def buildSearchUrl(job_search):
    """
    构造搜索URL
    """

    # 加载区域代码数据
    with open('queryParams.json', 'r', encoding='utf-8') as f:
        params_data = json.load(f)


    location_dicts = {}
    city_code_map = params_data["cityCode"]
    
    # 处理区域配置
    if job_search.get('areas'):
        # 处理明确指定的区域
        for city_name, districts in job_search['areas'].items():
            if city_name not in city_code_map:
                print(f"警告：未找到城市 [{city_name}] 的编码，已跳过")
                continue
            
            city_entry = city_code_map[city_name]
            city_code = list(city_entry.keys())[0]  # 获取城市编码
            
            valid_districts = []
            for district in districts:
                if district in city_entry[city_code]:
                    valid_districts.append(city_entry[city_code][district])
                else:
                    print(f"警告：城市 [{city_name}] 下未找到区域 [{district}]")
            
            if valid_districts:
                location_dicts.setdefault(city_code, []).extend(valid_districts)
    else:
        # 处理城市全集
        for city_name in job_search.get('city', []):
            if city_name not in city_code_map:
                print(f"警告：未找到城市 [{city_name}] 的编码，已跳过")
                continue
            
            city_entry = city_code_map[city_name]
            city_code = list(city_entry.keys())[0]
            # 获取该城市所有区域编码
            all_districts = list(city_entry[city_code].values())
            location_dicts[city_code] = all_districts

    # 参数验证
    if not location_dicts:
        raise ValueError("未找到有效的城市/区域配置")


    base_url = "https://www.zhipin.com/web/geek/job"

    # 转换到具体代码
    params_config = {
        'position': [str(params_data["position"][v]) for v in job_search.get("position", [])],
        'industry': [str(params_data["industry"][v]) for v in job_search.get("industry", [])],
        'experience': [str(params_data["experience"][v]) for v in job_search.get("experience", [])],
        'salary': [str(params_data["salary"][v]) for v in job_search.get("salary", [])],
        'jobType': [str(params_data["jobType"][v]) for v in job_search.get("jobType", [])],
        'scale': [str(params_data["scale"][v]) for v in job_search.get("scale", [])],
        'stage': [str(params_data["stage"][v]) for v in job_search.get("stage", [])],
        'query': list(job_search.get('query', ''))  # 保持单值列表形式
    }

    params_config={k: v for k, v in params_config.items() if v}

    # 生成基础参数组合
    param_combinations = []
    for city_code, districts in location_dicts.items():
        # 为每个城市生成区域组合
        for district in districts:
            
            current_params = {}

            current_params['city'] = city_code
            current_params['areaBusiness'] = district

            if not params_config:
                yield f"{base_url}?city={city_code}&areaBusiness={district}"
                continue

            # 递归生成参数组合
            def param_generator(keys, values, index=0, current_params=None):
                current_params = dict(base_params) if current_params is None else current_params.copy()
                if index == len(keys):
                    param_str = '&'.join(f"{k}={v}" for k, v in sorted(current_params.items()))
                    yield f"{base_url}?{param_str}"
                    
                else:
                    key = keys[index]
                    for value in values[index]:
                        current_params[key] = value
                        yield from param_generator(keys, values, index+1, current_params)
            
            # 添加其他参数组合
            parma_ksys=list(params_config.keys())
            parma_values=list(params_config.values())
            yield from param_generator(parma_ksys,parma_values,0,current_params)





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
            print(f"薪资格式错误 招聘岗位: {job_name} | {job_salary}")
            continue
        # 判断薪资是否满足条件
        if min_monthly_salary >= expectedSalary:
            jobsMatchingSalary.append(job)
        else:
            print(f"薪资太低 招聘岗位: {job_name} | {job_salary}")
    return jobsMatchingSalary   

def parseParams(link):
    """
    从招聘链接中提取关键参数
    
    参数:
        link (str): 完整的职位详情页链接
        
    返回:
        tuple | bool: 
            - 匹配成功时返回 (job_id, lid, security_id) 元组
            - 匹配失败时返回 None
            
    示例:
        >>> link = "https://www.zhipin.com/job_detail/419da3a603395bee1Hdz0tW4FVNZ.html?lid=6SYDWYE1Ifr.search.1&securityId=W0jkRYF6cmzz0"
        >>> extract_job_params_from_link(link)
        ('419da3a603395bee1Hdz0tW4FVNZ', '6SYDWYE1Ifr.search.1', 'W0jkRYF6cmzz0')
    """
    pattern = r'/job_detail/([^.]+)\.html\?lid=([^&]+)&securityId=([^&]+)'
    match = re.search(pattern, link)
    return match.groups() if match else None

def getUserInfo(driver):
    cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    headers = {
        'User-Agent': driver.execute_script("return navigator.userAgent;")
    }
    url="https://www.zhipin.com/wapi/zpuser/wap/getUserInfo.json"
    try:
        userInfo=requests.get(url,cookies=cookies_dict,headers=headers).json()
        userId=userInfo['zpData']['userId']
        userName=userInfo['zpData']['name']
        trueMan=userInfo['zpData']['trueMan']
        print(f"成功获取到用户信息: 用户名是：{userName},账号id是：{userId}")
        if not trueMan:
            print("警告：本账号已被BOSS直聘标记")
    except Exception as e:
        print("获取用户信息失败")
        print(e)
        return "UNKNOWN",None
    return userId, userInfo

def load_config(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)