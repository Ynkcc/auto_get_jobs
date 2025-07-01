# src/main.py
import asyncio
import logging
import logging.config

from .common.config_manager import ConfigManager
from .common.event_manager import event_manager
from .services.browser_manager import BrowserManager
from .core.job_filter import JobFilter
from .core.job_analyzer import JobAnalyzer
from .services.ws_client.client import WsClient
from .services.zhipin_api import zhipin_api
from .common.db_manager import DatabaseManager

# ... (LOGGING_CONFIG 不变) ...
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'encoding': 'utf-8', # 明确编码
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

stop_flag = asyncio.Event()
pause_event = asyncio.Event()
pause_event.set() 

# --- 新增事件处理器 ---
async def handle_stop_request(**kwargs):
    logger.info("主程序收到停止任务请求，设置停止标志。")
    stop_flag.set()

async def handle_pause_request(**kwargs):
    logger.info("主程序收到暂停任务请求，清除暂停事件（将导致阻塞）。")
    pause_event.clear()

async def handle_resume_request(**kwargs):
    logger.info("主程序收到继续任务请求，设置暂停事件（将解除阻塞）。")
    pause_event.set()

# **新增: 配置重载处理器**
async def handle_config_reload(**kwargs):
    """
    处理配置重载事件，重新初始化需要更新的模块。
    """
    logger.info("主程序收到配置重载请求，将重新初始化相关模块...")
    try:
        config = ConfigManager.get_config()
        # 重新初始化 ZhipinApi 的速率限制器
        zhipin_api.reinitialize_config()
        
        # 可以在这里添加更多模块的重载逻辑
        # 例如: job_filter = JobFilter(config)
        # job_analyzer = JobAnalyzer(config)
        
        logger.info("模块重载完成。")
    except Exception as e:
        logger.error(f"重载配置并重新初始化模块时出错: {e}", exc_info=True)


async def main():
    try:
        # **修改: 调用 get_config 会自动处理加载逻辑**
        config = ConfigManager.get_config()
        zhipin_api.reinitialize_config()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"启动失败: {e}")
        return

    logger.info("开始初始化所有模块...")
    db_manager = DatabaseManager(config.database.filename)
    browser_manager = BrowserManager(config, stop_flag, pause_event)
    job_filter = JobFilter(config)
    job_analyzer = JobAnalyzer(config)
    ws_client = WsClient(config, stop_flag)
    logger.info("所有模块初始化完成")

    logger.info("开始注册事件订阅者...")
    
    # --- 核心流程事件 ---
    event_manager.subscribe("cookies_updated", zhipin_api.handle_session_update)
    event_manager.subscribe("cookies_updated", ws_client._handle_cookies_updated)
    event_manager.subscribe("fetch_jobs_requested", browser_manager.start_fetching_jobs)
    event_manager.subscribe("job_list_found", job_analyzer.fetch_job_details)
    event_manager.subscribe("job_details_fetched", job_filter.pre_filter_jobs)
    event_manager.subscribe("job_details_fetched", db_manager.save_initial_jobs)
    event_manager.subscribe("jobs_pre_filtered", job_analyzer.process_job_list)
    event_manager.subscribe("job_analysis_complete", db_manager.update_job_analysis)
    
    # --- 沟通与投递流程事件 ---
    event_manager.subscribe("add_friend", ws_client.handle_add_friend)
    event_manager.subscribe("apply_to_job", ws_client.handle_application) 
    event_manager.subscribe("application_sent_successfully", db_manager.update_job_status_applied)
    
    # --- 任务控制事件 ---
    event_manager.subscribe("stop_fetch_requested", handle_stop_request)
    event_manager.subscribe("pause_fetch_requested", handle_pause_request)
    event_manager.subscribe("resume_fetch_requested", handle_resume_request)
    # **新增: 订阅配置重载事件**
    event_manager.subscribe("config_reloaded", handle_config_reload)

    # --- 关闭流程事件 ---
    event_manager.subscribe("shutdown", browser_manager.close)
    event_manager.subscribe("shutdown", ws_client.close)
    event_manager.subscribe("shutdown", job_filter.close)
    event_manager.subscribe("shutdown", job_analyzer.close)
    event_manager.subscribe("shutdown", zhipin_api.close)
    logger.info("事件订阅者注册完成")

    try:
        logger.info("启动核心服务...")
        
        ws_task = asyncio.create_task(ws_client.run())

        login_successful = await browser_manager.login_and_setup()

        if login_successful:
            logger.info("登录成功，程序进入待命状态。请在GUI界面操作。")
            await event_manager.publish("login_successful")
            await stop_flag.wait()
        else:
            logger.error("登录失败，程序即将退出。")
            stop_flag.set()
        
    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        logger.info("正在关闭所有服务...")
        if not stop_flag.is_set():
            stop_flag.set()
        
        if event_manager._listeners.get("shutdown"):
            shutdown_loop = asyncio.new_event_loop()
            try:
                shutdown_loop.run_until_complete(event_manager.publish("shutdown"))
            finally:
                shutdown_loop.close()

        await asyncio.sleep(3) 
        logger.info("程序已优雅退出")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("检测到Ctrl+C，程序开始退出...")
        stop_flag.set()