from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
from utils_database import DatabaseManager
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
    db_manager = DatabaseManager('jobs.db')
    recv_queue = Queue()
    comm_queue = Queue()
    done_event = Event()
    processor = JobProcessor(comm_queue,recv_queue,done_event)  # 传入db_queue
    
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
            #过滤访问过的
            valid_jobs = db_manager.filterVisited(valid_jobs)
            jobsDetails=None
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
                jobsDetails = recv_queue.get()
            #存放到数据库
            # save_jobs_to_csv(jobsDetails,"jobsDetails.csv")
            # save_jobs_to_csv(jobs,"jobs.csv")
            db_manager.save_jobs_details(jobs,jobsDetails)
            
            # 翻页逻辑
            time.sleep(15)
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