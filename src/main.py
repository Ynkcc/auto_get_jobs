from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException 
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
from multiprocessing import Process, Queue, Event
from utils.general import *
from utils.db_utils import DatabaseManager
from job_processor import JobProcessor

def login(driver,account):
    """
    登录BOSS直聘
    """
    account_name =account.get("username")
    login_file=f"./data/{account_name}.json"
    manager = SessionManager(driver, login_file)
    #登录URl
    login_url = "https://www.zhipin.com/web/user/?ka=header-login"
    driver.get(login_url)

    #等待用户登录
    print(f"等待登陆...")
    #加载cookies
    if manager.load():
        driver.refresh()
    try:
        WebDriverWait(driver, timeout="600").until(
                EC.presence_of_element_located((By.XPATH, '//a[@ka="header-username"]'))
            )
    except TimeoutException:
        driver.quit()
        print("登录超时，程序自动退出")
    manager.start_autosave()
    print(f"登陆成功。")
    return manager

def main_loop(driver, config):

    # 从配置中获取参数
    databaseFileName = config['database']['filename']
    job_search =config['job_search']
    crawler_config = config['crawler']
    page_load_timeout=crawler_config.get("page_load_timeout", 60)
    next_page_delay=crawler_config.get("next_page_delay", 5)
    minSalary,_ = config["job_check"]["salary_range"]

    userId, _ =getUserInfo(driver)
    db_manager = DatabaseManager(databaseFileName,userId)
    recv_queue = Queue()
    comm_queue = Queue()
    done_event = Event()
    processor = JobProcessor(comm_queue,recv_queue,done_event,config)  # 传入db_queue
    
    # 启动处理进程
    process = Process(target=processor.start_processing)
    process.start()

    try:
        for targetUrl in buildSearchUrl(job_search):

            driver.get(targetUrl)            
            while True:
                try:
                    # 等待页面加载
                    WebDriverWait(driver, page_load_timeout).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "job-card-wrapper"))
                    )
                except TimeoutException:
                    print("获取页面职位超时，可能无岗位或被封禁")
                    break
                # 获取并过滤当前页职位
                jobs = getPageJobsInfo(driver)
                valid_jobs = filterJobsBySalary(jobs, minSalary)
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
                time.sleep(next_page_delay)
                if not nextPage(driver):
                    break

    finally:
        # 发送终止信号并等待进程结束
        comm_queue.put(None)
        process.join(timeout=30)


def main():
    config=load_config("config/config.yaml")
    driver=init_driver(config['crawler']["webdriver"])
    for account in config['accounts']:
        manager=login(driver,account)
        main_loop(driver,config)
        manager.stop_autosave()
        manager.clear_data()


if __name__=="__main__":
    main()