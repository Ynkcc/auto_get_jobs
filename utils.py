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
