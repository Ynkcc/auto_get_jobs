from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import random
import time
import json
from utils import *
from multiprocessing import Process, Queue, Event
from job_processor import JobProcessor

load_dotenv()

def login(driver):
    """
    登录BOSS直聘
    """

    #登录URl
    login_url = "https://www.zhipin.com/web/user/?ka=header-login"
    driver.get(login_url)

    #等待用户登录
    print(f"等待登陆...")
    #加载cookies
    if load_login_data(driver):
        driver.get(login_url)

    WebDriverWait(driver, timeout="600").until(
            EC.presence_of_element_located((By.XPATH, '//a[@ka="header-username"]'))
        )

    # 登录成功后保存登录数据
    save_login_data(driver)
    #启动一个线程来定期保存
    start_cookie_saver(driver)
    print(f"登陆成功。")

def main_loop(driver, extraData):
    comm_queue = Queue()  # 用于发送任务批次
    done_event = Event()  # 用于同步处理完成
    processor = JobProcessor(comm_queue, done_event)
    
    # 启动处理进程
    process = Process(target=processor.start_processing)
    process.start()

    try:
        targetUrl = buildSearchUrl(extraData["query"], extraData["city"])
        driver.get(targetUrl)
        
        while True:
            # 等待页面加载
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-card-wrapper"))
            )
            
            # 获取并过滤当前页职位
            jobs = getPageJobsInfo(driver)
            valid_jobs = filterJobsBySalary(jobs, extraData["expectedSalary"])
            if valid_jobs:

                # 获取 cookies 和 headers
                cookies = driver.get_cookies()
                cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                headers = {
                    'User-Agent': driver.execute_script("return navigator.userAgent;")
                }
                # 发送当前批次任务
                comm_queue.put({
                    "jobs": valid_jobs,
                    "cookies": cookies_dict,
                    "headers": headers
                })
                done_event.clear()  # 重置事件状态
                
                # 等待本批次处理完成
                while not done_event.wait(timeout=60):
                    print("Waiting for batch processing...")
                    time.sleep(5)
                    
            # 翻页逻辑
            time.sleep(3)
            if not nextPage(driver):
                break
                
    finally:
        # 发送终止信号并等待进程结束
        comm_queue.put(None)
        process.join(timeout=30)


def main():
    driver=init_driver()
    login(driver)
    # while True:
    #     time.sleep(3)
    extraData={
        "query":"运维",
        "city":"海口",
        "expectedSalary":6
    }

    main_loop(driver,extraData)

if __name__=="__main__":
    main()