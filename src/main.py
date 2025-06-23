# src/main.py
import asyncio
import signal
import logging
import logging.config

from .common.config_manager import ConfigManager
from .common.event_manager import event_manager
from .browser_manager import BrowserManager
from .core.job_filter import JobFilter
from .core.job_analyzer import JobAnalyzer
from .services.ws_client.client import WsClient
from .common.db_manager import DatabaseManager
from .services.zhipin_api import zhipin_api # 导入新的API管理器

# --- 日志配置 (保持不变) ---
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
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# 初始化配置管理器
ConfigManager.load_config()
config = ConfigManager.get_config()
stop_flag = asyncio.Event()

def signal_handler(sig, frame):
    logger.info(f"接收到停止信号 {sig}, 正在准备关闭...")
    if not stop_flag.is_set():
        stop_flag.set()

async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. 初始化所有模块
    logger.info("开始初始化所有模块...")
    await zhipin_api.initialize() # 初始化API管理器并订阅事件
    db_manager = DatabaseManager(config.database.filename)
    browser_manager = BrowserManager(config, stop_flag)
    job_filter = JobFilter(config)
    job_analyzer = JobAnalyzer(config)
    ws_client = WsClient(config, stop_flag)
    logger.info("所有模块初始化完成")

    # 2. 注册事件订阅者
    logger.info("开始注册事件订阅者...")
    
    # 浏览器发现职位列表后，进行前置筛选和初始入库
    event_manager.subscribe("job_list_found", job_filter.pre_filter_jobs)
    event_manager.subscribe("job_list_found", db_manager.save_initial_jobs)

    # 前置筛选完成后，进行AI分析
    event_manager.subscribe("jobs_pre_filtered", job_analyzer.process_job_list)

    # 职位分析完成后，更新数据库
    event_manager.subscribe("job_analysis_complete", db_manager.update_job_analysis)
    
    # 决定投递职位时，发起沟通
    event_manager.subscribe("add_friend", ws_client.handle_add_friend)
    # 沟通成功后，发送问候语和简历
    event_manager.subscribe("apply_to_job", ws_client.handle_application) 

    # 投递成功后，更新数据库状态
    event_manager.subscribe("application_sent_successfully", db_manager.update_job_status_applied)
    
    # 程序关闭时，清理所有模块资源
    event_manager.subscribe("shutdown", browser_manager.close)
    event_manager.subscribe("shutdown", ws_client.close)
    event_manager.subscribe("shutdown", job_filter.close)
    event_manager.subscribe("shutdown", job_analyzer.close)
    event_manager.subscribe("shutdown", zhipin_api.close) # 新增：关闭API管理器的会话
    logger.info("事件订阅者注册完成")

    try:
        # 3. 启动核心任务
        logger.info("启动核心服务...")
        ws_task = asyncio.create_task(ws_client.run())
        browser_task = asyncio.create_task(browser_manager.start())
        await stop_flag.wait()
        
    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        logger.info("正在关闭所有服务...")
        await event_manager.publish("shutdown")
        await asyncio.sleep(3) 
        logger.info("程序已优雅退出")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("检测到Ctrl+C，程序退出")