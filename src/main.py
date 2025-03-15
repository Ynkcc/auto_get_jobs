# File: main.py
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
        backupCount=5,  # 保持5个备份文件
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 获取根日志器并配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 获取 selenium remote connection 的 logger 并设置 level 为 WARNING
    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.WARNING)
    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    urllib3_logger.setLevel(logging.WARNING)
setup_logging(logging_config)
logger = logging.getLogger(__name__)
logger.info("test")

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import sys
from queue import Queue
import threading
from utils.general import *
from utils.db_utils import DatabaseManager
from job_handler import JobHandler
from ws_client.ws_client import WsClient
from utils.session_manager import SessionManager
import asyncio
import concurrent.futures
import signal
import sys

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

stop_flag = asyncio.Event()

def signal_handler(sig, frame):
    logging.info(f"接收到信号 {sig}, 设置停止标志")
    stop_flag.set()

signal.signal(signal.SIGINT, signal_handler)

def login(driver, account):
    """
    登录BOSS直聘
    """
    account_name =account.username
    login_file=f"./data/{account_name}.json"
    manager = BrowserSessionHandler(driver, login_file)
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

def main(config):
    driver = init_driver(config.crawler.webdriver)

    # 创建共享队列和事件
    job_queue = Queue()
    job_done = threading.Event()
    ws_queue = Queue()
    ws_done = threading.Event()
    running_event = threading.Event()

    # 初始化并启动线程
    running_event.set()
    ws_done.set()
    jobhandler = JobHandler(
        job_queue=job_queue,
        ws_queue=ws_queue,
        done_event=job_done,
        running_event=running_event,
    )

    # 创建事件循环
    loop = asyncio.new_event_loop()
    # 创建一个子线程
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    loop.run_in_executor(executor, start_loop, loop)

    ws_client = WsClient(
        recv_queue=ws_queue,
        publish_done=ws_done,
        running_event=running_event,
        loop=loop
    )

    jobhandler.start()
    ws_client.start()

    for account in config.accounts:
        manager = login(driver, account)

        try:
            url_list=list(build_search_url(config.job_search))
            i = 1
            total=len(url_list)
            for url in url_list:
                logger.info(f"当前第{i}个url，共{total}个")
                i+=1
                driver.get(url)
                while True:
                    try:
                        # 等待页面加载
                        WebDriverWait(driver, config.crawler.page_load_timeout).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "job-card-wrapper"))
                        )
                    except TimeoutException:
                        print("获取页面职位超时，可能无岗位或被封禁")
                        break

                    jobs = get_page_jobs_info(driver)
                    cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                    headers = {
                        'User-Agent': driver.execute_script("return navigator.userAgent;")
                    }
                    SessionManager.update_session(cookies, headers)
                    job_queue.put(["tasks",jobs])
                    time.sleep(config.crawler.next_page_delay)
                    if stop_flag.is_set():
                        logging.info("接收到停止信号，程序将在30s内退出")
                        ws_done.wait(30)
                        sys.exit(0)
                    if not next_page(driver):
                        break

        finally:
            job_queue.join()
            ws_queue.join()
            ws_done.wait() # 等待所有 MQTT 消息发送完成
            manager.stop_autosave()
            manager.clear_data()

if __name__=='__main__':
    main(config)
