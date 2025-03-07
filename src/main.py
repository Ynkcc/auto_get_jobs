from utils.config_manager import ConfigManager
import logging
from logging.handlers import RotatingFileHandler

# 加载配置
ConfigManager.load_config("config/config.yaml")
config = ConfigManager.get_config()

# 配置日志
logging_config = config.logging
# 修改 main.py 中的 setup_logging 函数
def setup_logging(logging_config):
    """
    配置日志系统
    """
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_config.level)
    console_handler.setFormatter(formatter)

    # 文件处理器（使用 RotatingFileHandler 替代 FileHandler）
    file_handler = RotatingFileHandler(
        filename=logging_config.path,
        mode='a',
        maxBytes=logging_config.max_size * 1024 * 1024,  # 转换为字节
        backupCount=5  # 保持5个备份文件
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 获取根日志器并配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

setup_logging(logging_config)
logger = logging.getLogger(__name__)
logger.info("test")

from selenium.common.exceptions import TimeoutException
import sys
from utils.general import *
from utils.db_utils import DatabaseManager
from job_processor import JobProcessor

def login(driver, account):
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
        sys.exit(1)
    manager.start_autosave()
    print(f"登陆成功。")
    return manager

def main(driver, config):
    # 初始化WebDriver
    driver = init_driver(config.crawler.webdriver)

    for account in config.accounts:
        manager = login(driver, account)
        main_loop(driver, config)
        manager.stop_autosave()
        manager.clear_data()

    resume_image_dict=None
    if send_resume_image and os.path.exists(resume_image_file):
        resume_image_dict=upload_image(driver,resume_image_file)
    
    userId, _ =getUserInfo(driver)
    db_manager = DatabaseManager(databaseFileName,userId)
    recv_queue = Queue()
    comm_queue = Queue()
    done_event = Event()
    processor = JobProcessor(comm_queue,recv_queue,done_event,config,resume_image_dict)  # 传入db_queue
    
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
                valid_jobs = db_manager.filterVisited(valid_jobs,userId)
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

if __name__=='__main__':
    main()