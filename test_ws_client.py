# test_ws_client.py
import asyncio
import signal
import logging
import logging.config

# --- 核心模块导入 ---
# 确保你的项目结构能让此脚本找到 src 目录
# 如果在根目录运行，可以使用下面的方式，否则请调整 sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.common.config_manager import ConfigManager
from src.common.event_manager import event_manager
from src.browser_manager import BrowserManager
from src.services.ws_client.client import WsClient
from src.services.zhipin_api import zhipin_api

# --- 日志配置 (使用详细的 DEBUG 级别以便于诊断) ---
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
            'level': 'DEBUG',  # 设置为 DEBUG
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("WsClientTester")

# --- 全局停止标志 ---
stop_flag = asyncio.Event()

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    logger.info(f"接收到停止信号 {sig}, 正在准备关闭...")
    if not stop_flag.is_set():
        stop_flag.set()

async def application_success_handler(job_data: dict, **kwargs):
    """投递成功后的回调，用于确认流程走完"""
    job_name = job_data.get("jobInfo", {}).get("jobName", "未知职位")
    logger.info(f"🎉🎉🎉 投递流程已成功完成，目标职位: {job_name} 🎉🎉🎉")
    # 等待一会后自动停止测试
    await asyncio.sleep(5)
    stop_flag.set()

# --- 测试核心逻辑 ---
async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. 初始化配置
    logger.info("初始化配置管理器...")
    ConfigManager.load_config()
    config = ConfigManager.get_config()
    zhipin_api.reinitialize_config()

    # 2. 定义你要投递的固定岗位信息
    # !! 重要: 请替换下面的所有 "xxxx" 值为真实数据 !!
    # 如何获取?
    #   - 打开浏览器开发者工具 (F12)
    #   - 访问一个职位详情页面
    #   - 在网络(Network)面板中，筛选 "job/detail.json"，查看其响应(Response)
    #   - `encryptJobId`, `lid`, `securityId` 等信息都在响应的 `zpData` 中。
    #   - `encryptUserId` 在 `zpData.bossInfo.encryptUserId` 中。
    test_job_data = {
        "jobInfo": {
            "encryptId": "在此处替换为真实岗位的 encryptJobId",  # 例如: "1b2c3d4e5f..."
            "jobName": "后端开发工程师 (测试专用)",
            "salaryDesc": "20-40K",
            # ... 其他 jobInfo 字段 (可选)
        },
        "bossInfo": {
            "encryptUserId": "在此处替换为真实 Boss 的 encryptUserId", # 例如: "6a7b8c9d0e..."
            # ... 其他 bossInfo 字段 (可选)
        },
        "brandComInfo": {
            "brandName": "未来无限科技 (测试公司)",
            # ... 其他 brandComInfo 字段 (可选)
        },
        "lid": "在此处替换为真实岗位的 lid", # 例如: "k9j8h7g6f5..."
        "securityId": "在此处替换为真实岗位的 securityId" # 例如: "abcdefg-hijklmn-opqrst-uvwxyz123"
    }

    # # 检查占位符是否已被替换
    # if "在此处替换" in str(test_job_data):
    #     logger.error("请先在脚本中替换 `test_job_data` 的占位符信息！")
    #     return

    # 3. 初始化核心模块
    logger.info("初始化浏览器、API客户端和WsClient...")
    browser_manager = BrowserManager(config, stop_flag)
    ws_client = WsClient(config, stop_flag)

    # 4. 注册测试所需的事件
    logger.info("注册事件订阅...")
    # a. 会话同步: Browser -> ZhipinApi
    event_manager.subscribe("cookies_updated", zhipin_api.handle_session_update)
    # b. 沟通与投递: TestScript -> WsClient
    event_manager.subscribe("add_friend", ws_client.handle_add_friend)
    event_manager.subscribe("apply_to_job", ws_client.handle_application)
    # c. 投递成功确认: WsClient -> TestScript
    event_manager.subscribe("application_sent_successfully", application_success_handler)
    # d. 优雅关闭
    event_manager.subscribe("shutdown", browser_manager.close)
    event_manager.subscribe("shutdown", zhipin_api.close)
    event_manager.subscribe("shutdown", ws_client.close)
    logger.info("事件订阅完成")

    try:
        # 5. 启动核心任务
        logger.info("启动浏览器进行登录...")
        browser_task = asyncio.create_task(browser_manager.start())
        
        logger.info("等待 ZhipinApi 会话就绪...")
        await zhipin_api.wait_for_ready()
        logger.info("ZhipinApi 已就绪! 启动 WsClient...")

        ws_task = asyncio.create_task(ws_client.run())
        
        # 6. 等待 WsClient 连接成功
        while not ws_client.is_connected:
            if stop_flag.is_set():
                logger.warning("在WsClient连接前收到停止信号，测试终止")
                return
            logger.info("等待 WsClient 连接...")
            await asyncio.sleep(1)
        
        logger.info("✅ WsClient 已成功连接! 准备开始投递测试...")
        await asyncio.sleep(2) # 等待一下，确保稳定

        # 7. 发布 `add_friend` 事件，启动投递流程
        logger.info(f"发布 'add_friend' 事件，目标职位: {test_job_data['jobInfo']['jobName']}")
        await event_manager.publish("add_friend", job_data=test_job_data)

        # 8. 等待测试完成或被手动停止
        logger.info("投递流程已启动，等待其完成或手动按 Ctrl+C 停止...")
        await stop_flag.wait()

    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        logger.info("正在关闭所有服务...")
        # 确保即使浏览器任务提前结束，也能触发关闭流程
        if not stop_flag.is_set():
            stop_flag.set()
        await event_manager.publish("shutdown")
        # 等待所有异步的 close 方法执行完毕
        await asyncio.sleep(3)
        logger.info("测试脚本已优雅退出")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("检测到Ctrl+C，程序退出")