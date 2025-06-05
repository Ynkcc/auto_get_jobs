# File: main.py
from utils.config_manager import ConfigManager
import logging
from logging.handlers import RotatingFileHandler
import json # 导入 json 模块

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

    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    urllib3_logger.setLevel(logging.WARNING)
setup_logging(logging_config)
logger = logging.getLogger(__name__)

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
from playwright.async_api import async_playwright, TimeoutError, Page, Response

async def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

stop_flag = asyncio.Event()

def signal_handler(sig, frame):
    logging.info(f"接收到信号 {sig}, 设置停止标志")
    stop_flag.set()

signal.signal(signal.SIGINT, signal_handler)

async def login(page, account,loop):
    """
    登录BOSS直聘
    """
    account_name =account.username
    login_file=f"./data/{account_name}.json"
    manager = BrowserSessionHandler(page, login_file,loop)
    #登录URl
    login_url = "https://www.zhipin.com/web/user/?ka=header-login"
    await page.goto(login_url)

    #等待用户登录
    print(f"等待登陆...")
    #加载cookies
    if await manager.load():
        for i in range(3):  # Retry up to 3 times
            try:
                await page.reload()
                break  # If successful, break the loop
            except Exception as e:
                print(f"页面加载失败: {e}, 尝试重新加载页面 ({i+1}/3)")
        else:
            print("页面加载多次失败，程序可能无法正常登录")
    try:
        await page.locator('a[ka="header-username"]').wait_for(timeout=600000) # timeout in milliseconds
    except TimeoutError:
        print("登录超时，程序自动退出")
        # page.context.browser.close() # close browser context instead of driver
        sys.exit(1)
    await manager.start_autosave()
    logger.info(f"登陆成功。")
    return manager

async def main(config):
    page = await init_driver(config.crawler.playwright)

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

    loop = asyncio.get_running_loop()
    ws_client = WsClient(
        recv_queue=ws_queue,
        publish_done=ws_done,
        running_event=running_event,
        loop=loop
    )

    jobhandler.start()
    ws_client.start()

    for account in config.accounts:
        manager = await login(page, account, loop)
        try:
            url_list = build_search_url(config.job_search)
            i = 1
            total=len(url_list)

            for url in url_list:
                logger.info(f"开始处理第 {i}/{total} 个URL: {url}")
                i+=1

                # --- 新增：用于存储从API获取的数据 ---
                api_jobs_data = []
                has_more_data = True # 初始假设有数据
               

                # --- 新增：Response 监听器处理函数 ---
                async def handle_response(response: Response):
                    nonlocal api_jobs_data, has_more_data # 允许修改外部变量
                    # 检查URL是否匹配目标API
                    if "wapi/zpgeek/search/joblist.json" in response.url:
                        logger.debug(f"监听到接口响应: {response.url}")
                        try:
                            # 尝试获取JSON数据
                            data = await response.json()
                            # 检查返回码
                            if data.get("code") == 0 and "zpData" in data:
                                zp_data = data["zpData"]
                                job_list = zp_data.get("jobList", [])
                                has_more = zp_data.get("hasMore", False)
                                total_count = zp_data.get("totalCount", 0)
                                logger.info(f"接口返回 {len(job_list)} 个岗位, hasMore: {has_more}, totalCount: {total_count}")

                                # --- 数据转换 ---
                                processed_jobs = []
                                for item in job_list:
                                    # 构建 job_link
                                    encryptJobId = item.get("encryptJobId")
                                    lid = item.get("lid")
                                    securityId = item.get("securityId")
                                    if not all([encryptJobId, lid, securityId]):
                                        logger.warning(f"缺少必要ID，无法构建链接: {item.get('jobName')}")
                                        continue

                                    # 注意：lid 可能包含 itemId，需要处理
                                    # 简单的处理方式是只取 ? 前的部分，但更可靠的是从原始URL或API参数获取
                                    # 这里暂时用原始 lid
                                    job_link = f"/job_detail/{encryptJobId}.html?lid={lid}&securityId={securityId}"

                                    # 映射字段
                                    processed_job = {
                                        'job_name': item.get('jobName'),
                                        'job_salary': item.get('salaryDesc'),
                                        'job_link': job_link,
                                        'company_name': item.get('brandName'),
                                        # company_tags 需要从 jobLabels 或 skills 映射，这里简化处理
                                        'company_tags': item.get('jobLabels', []) + item.get('skills', [])
                                    }
                                    processed_jobs.append(processed_job)

                                # 将处理后的数据添加到列表
                                api_jobs_data.extend(processed_jobs)
                                # 更新 hasMore 状态
                                has_more_data = has_more
                            else:
                                logger.error(f"接口响应错误: code={data.get('code')}, message={data.get('message')}")
                                # 可以选择在这里停止，或者标记为没有更多数据
                                has_more_data = False
                        except json.JSONDecodeError:
                            logger.error(f"无法解析JSON响应: {response.url}")
                            has_more_data = False
                        except Exception as e:
                            logger.error(f"处理响应时出错 {response.url}: {e}")
                            has_more_data = False
                    # --- 结束 Response 监听器处理函数 ---

                # --- 注册监听器 ---
                page.on("response", handle_response)

                # --- 导航到页面 ---
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=config.crawler.page_load_timeout * 1000)
                except TimeoutError:
                    logger.error(f"页面加载超时: {url}")
                    page.remove_listener("response", handle_response) # 移除监听器
                    continue # 跳过这个URL
                except Exception as e:
                    logger.error(f"导航到页面时出错 {url}: {e}")
                    page.remove_listener("response", handle_response) # 移除监听器
                    continue # 跳过这个URL


                # --- 循环处理分页（通过滚动） ---
                while has_more_data:
                    # 处理当前已获取的数据
                    if api_jobs_data:
                        logger.info(f"处理 {len(api_jobs_data)} 个已获取的岗位...")
                        # 更新会话信息 (cookies, headers)
                        cookies = {cookie['name']: cookie['value'] for cookie in await page.context.cookies()}
                        headers = {'User-Agent': await page.evaluate("() => navigator.userAgent")}
                        SessionManager.update_session(cookies, headers)

                        # 将数据放入处理队列
                        job_queue.put(["tasks", list(api_jobs_data)]) # 发送副本
                        api_jobs_data.clear() # 清空，准备接收下一批
                        job_queue.join() # 等待处理完成

                        # 检查停止标志
                        if stop_flag.is_set():
                            logging.info("接收到停止信号，程序将在30s内退出")
                            ws_done.wait(30)
                            page.remove_listener("response", handle_response) # 移除监听器
                            await page.context.close()
                            sys.exit(0)

                    # 如果 API 显示还有更多数据，则滚动页面
                    if has_more_data:
                        logger.info("滚动页面以加载更多数据...")
                        await page.mouse.wheel(0, 1000)
                        await page.wait_for_timeout(5000)
                       
                    else:
                        logger.info("没有更多数据，结束当前URL的处理。")
                        break # 跳出内层 while 循环

                # --- 处理最后一批数据（如果滚动后还有剩余） ---
                if api_jobs_data:
                    logger.info(f"处理最后一批 {len(api_jobs_data)} 个岗位...")
                    cookies = {cookie['name']: cookie['value'] for cookie in await page.context.cookies()}
                    headers = {'User-Agent': await page.evaluate("() => navigator.userAgent")}
                    SessionManager.update_session(cookies, headers)
                    job_queue.put(["tasks", list(api_jobs_data)])
                    api_jobs_data.clear()
                    job_queue.join()

                # --- 移除监听器 ---
                page.remove_listener("response", handle_response)
                logger.info(f"完成处理URL: {url}")
                await asyncio.sleep(config.crawler.next_page_delay) # 不同 URL 之间的延迟


        finally:
            job_queue.join()
            ws_queue.join()
            ws_done.wait() # 等待所有 MQTT 消息发送完成
            if manager: # 确保 manager 已成功初始化
                await manager.stop_autosave()
                await manager.clear_data()
            if page and page.context: # 确保页面和上下文存在
                await page.context.close()

    running_event.clear()
    if config.database.export_excel:
        export_to_xlsx(config.database.filename, config.database.excel_path)
    sys.exit(0)

if __name__=='__main__':
    asyncio.run(main(config))