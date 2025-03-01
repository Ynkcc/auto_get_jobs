from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import json
import os
import re
import threading
import pandas as pd
import time

LOGIN_DATA_FILE = "login_data.json"

def saveLoginData(driver):
    loginData = {
        "cookies": driver.get_cookies(),
        "localStorage": driver.execute_script("return Object.assign({}, window.localStorage);"),
        "sessionStorage": driver.execute_script("return Object.assign({}, window.sessionStorage);")
    }
    with open(LOGIN_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(loginData, f, ensure_ascii=False, indent=4)

def loadLoginData(driver):
    try:
        with open(LOGIN_DATA_FILE, "r", encoding="utf-8") as f:
            loginData = json.load(f)
        
        driver.delete_all_cookies()
        for cookie in loginData["cookies"]:
            driver.add_cookie(cookie)
            
        for k, v in loginData["localStorage"].items():
            driver.execute_script(f"window.localStorage.setItem('{k}', '{v}');")
            
        for k, v in loginData["sessionStorage"].items():
            driver.execute_script(f"window.sessionStorage.setItem('{k}', '{v}');")
            
        return True
    except FileNotFoundError:
        return False

def initDriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 防止被检测为自动化工具
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.set_capability('goog:loggingPrefs', {'performance': 'OFF'})  # 关闭性能日志
    options.add_argument('--log-level=3')  # 只记录严重错误
    driver_path = os.path.join("chromedriver", "chromedriver.exe")
    driver = webdriver.Chrome(service=Service(driver_path),options=options)

    return driver

def buildSearchUrl(query, city):
    with open("city_list.json", "r", encoding="utf-8") as f:
        cityId = json.load(f)[city]
    return f"https://www.zhipin.com/web/geek/job?query={query}&city={cityId}"

def filterJobsBySalary(jobs, expectedSalary):
    filtered = []
    for job in jobs:
        salary = re.sub(r'·\d+薪', '', job['job_salary'])
        
        if '元/天' in salary:
            daily = [int(x) for x in salary.replace('元/天', '').split('-')]
            monthly = [x * 22 / 1000 for x in daily]
        elif 'K' in salary or 'k' in salary:
            monthly = [float(x) for x in salary.upper().replace('K', '').split('-')]
        else:
            continue
            
        if min(monthly) >= expectedSalary:
            filtered.append(job)
    return filtered

def startCookieSaver(driver, interval=60):
    def saver():
        while True:
            saveLoginData(driver)
            time.sleep(interval)
            
    thread = threading.Thread(target=saver, daemon=True)
    thread.start()

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

