# test_ws_client.py
import asyncio
import logging
import json
import os

# 确保脚本可以从根目录找到src模块
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.services.ws_client.client import WsClient
from src.common.config_manager import ConfigManager
from src.common.event_manager import event_manager
from src.services.zhipin_api import zhipin_api

# --- 1. 基本配置 ---
# 配置日志，方便观察过程
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# 屏蔽一些第三方库的冗余日志
logging.getLogger('websockets').setLevel(logging.WARNING)
logging.getLogger('paho').setLevel(logging.WARNING)
logger = logging.getLogger("WS_CLIENT_TEST")

# --- 2. 准备测试数据 ---
# !!! 警告: 请务必在运行前替换下方所有 "xxxxxxxx" 为一个真实、有效且未投递过的岗位ID信息。
# 你可以通过浏览器开发者工具抓取API请求来获取这些ID。
FIXED_JOB_DATA_JSON = '''
{

        "pageType": 0,
        "selfAccess": false,
        "securityId": "w1cYVBhAEjwQ4-M1U0ZI31PJeHliYk9NGM54WJIOHpDhrbgONbJ1HHuyT2ykwVS_PmGctrpFqhrZE3-aajdmYco03iZGygRSpePRNxyhi4dN33uYQd24Z2GgaoY0hrx2neN50335wZPq9DlCZX1R29SN2NFX_A~~",
        "sessionId": null,
        "lid": "4C2BUgdCrka.search.4",
        "jobInfo": {
            "encryptId": "df22f9b990ba49f81Hx_3Nq4EVpZ",
            "encryptUserId": "89b9fc4097c345460XN82tW5F1RU",
            "invalidStatus": false,
            "jobName": "IT技术支持",
            "position": 100405,
            "positionName": "IT技术支持",
            "location": 101310100,
            "locationName": "海口",
            "experienceName": "1-3年",
            "degreeName": "大专",
            "jobType": 0,
            "proxyJob": 0,
            "proxyType": 0,
            "salaryDesc": "5-10K",
            "payTypeDesc": null,
            "postDescription": "工作内容\\n1、为企业内部用户提供专业的IT技术支持与服务。\\n2、参与售前与售后技术支持活动，确保技术问题得到有效解决。\\n3、与团队合作，共同维护和优化IT系统。\\n\\n任职要求\\n1、具备扎实的IT技术支持背景，能够独立处理技术难题。\\n2、熟悉计算机或通信领域的技术标准和操作流程。\\n3、具有良好的团队合作精神和客户服务意识。",
            "encryptAddressId": "4b402f397614f6d71nZ80ty-GVpTw4-5VPuc",
            "address": "海口龙华区海口市新华信息产业孵化园(新华南路)5层",
            "longitude": 110.344014,
            "latitude": 20.03833,
            "staticMapUrl": "https://img.bosszhipin.com/beijin/upload/amap_proxy/20231018/48ba41acc9cef1bf5789e45458daa1285cddf899145be7b86bb61e3b7bce0931da574d19d1d82c88.png.webp",
            "pcStaticMapUrl": "https://img.bosszhipin.com/beijin/upload/amap_proxy/20240511/48ba41acc9cef1bf053dc1dd79ba449ab369ba22d30fadfa6bb61e3b7bce0931da574d19d1d82c88.png.webp",
            "baiduStaticMapUrl": "",
            "baiduPcStaticMapUrl": "",
            "overseasAddressList": [],
            "overseasInfo": null,
            "showSkills": [
                "企业内部IT技术支持",
                "IT技术支持经验",
                "售前/售后技术支持",
                "计算机/通信相关专业"
            ],
            "anonymous": 0,
            "jobStatusDesc": "招聘中"
        },
        "bossInfo": {
            "name": "冯先生",
            "title": "招聘者",
            "tiny": "https://img.bosszhipin.com/boss/avatar/avatar_6.png",
            "large": "https://img.bosszhipin.com/boss/avatar/avatar_6.png",
            "activeTimeDesc": "4月内活跃",
            "bossOnline": false,
            "brandName": "小贝科技",
            "bossSource": 0,
            "certificated": true,
            "tagIconUrl": null,
            "avatarStickerUrl": null
        },
        "brandComInfo": {
            "encryptBrandId": "bd103f6e30af5c721HN40tW6EVc~",
            "brandName": "小贝科技",
            "logo": "https://img.bosszhipin.com/beijin/icon/894ce6fa7e58d64d57e7f22d2f3a9d18afa7fcceaa24b8ea28f56f1bb14732c0.png",
            "stage": 0,
            "stageName": "",
            "scale": 302,
            "scaleName": "20-99人",
            "industry": 100020,
            "industryName": "互联网",
            "introduce": "",
            "labels": [],
            "activeTime": 1748198086909,
            "visibleBrandInfo": true,
            "focusBrand": false,
            "customerBrandName": "小贝科技",
            "customerBrandStageName": ""
        },
        "oneKeyResumeInfo": {
            "inviteType": 0,
            "alreadySend": false,
            "canSendResume": false,
            "canSendPhone": false,
            "canSendWechat": false
        },
        "relationInfo": {
            "interestJob": false,
            "beFriend": false
        },
        "handicappedInfo": null,
        "appendixInfo": {
            "canFeedback": false,
            "chatBubble": null
        },
        "atsOnlineApplyInfo": {
            "inviteType": 0,
            "alreadyApply": false
        },
        "certMaterials": []
    }

'''
FIXED_JOB_DATA= json.loads(FIXED_JOB_DATA_JSON, strict=False)

# 指定包含cookies的账号文件
ACCOUNT_FILE = 'data/account1.json'


async def run_test():


    # 1. 初始化所有模块
    logger.info("开始初始化所有模块...")

    # 2. 注册事件订阅者 (新的事件流)
    logger.info("开始注册事件订阅者...")
    
    # BrowserManager定时发布的会话更新事件，由ZhipinApi处理
    event_manager.subscribe("cookies_updated", zhipin_api.handle_session_update)


    event_manager.subscribe("shutdown", zhipin_api.close)
    logger.info("事件订阅者注册完成")
    """执行完整的投递测试流程"""
    logger.info("="*20 + " WebSocket客户端投递测试 " + "="*20)
    
    # --- 3. 初始化环境 ---
    try:
        ConfigManager.load_config('config/config.yaml')
        config = ConfigManager.get_config()
        zhipin_api.reinitialize_config()
        logger.info("配置加载成功。")
    except Exception as e:
        logger.error(f"加载配置 'config/config.yaml' 失败: {e}")
        return

    # 创建停止标志和WsClient实例
    stop_flag = asyncio.Event()
    ws_client = WsClient(config, stop_flag)
    # 订阅 cookies 更新事件，由 WsClient 处理
    event_manager.subscribe("cookies_updated", ws_client._handle_cookies_updated)
    # 模拟BrowserManager，从文件加载cookies并初始化ZhipinApi
    try:
        with open(ACCOUNT_FILE, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
        if "headers" not in account_data:
            account_data["headers"] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
        # 发布事件，让ZhipinApi更新会话并进入就绪状态
        await event_manager.publish("cookies_updated", cookies_data=account_data)
        logger.info(f"已从 '{ACCOUNT_FILE}' 加载账号信息并初始化API。")
    except FileNotFoundError:
        logger.error(f"账号文件未找到: '{ACCOUNT_FILE}'。测试无法继续。")
        return
    except Exception as e:
        logger.error(f"初始化API会话失败: {e}", exc_info=True)
        return

    # 启动 WsClient 的主循环任务
    ws_task = asyncio.create_task(ws_client.run())

    # --- 4. 执行测试 ---
    logger.info("正在等待WsClient连接服务器... (最长等待15秒)")
    # 等待 WsClient 内部的 is_connected 标志位变为 True
    for _ in range(15):
        if ws_client.is_connected:
            break
        await asyncio.sleep(1)
    
    if not ws_client.is_connected:
        logger.error("WsClient未能连接，测试终止。请检查网络、账号凭据或WsClient的实现。")
    else:
        logger.info("WsClient已成功连接服务器。现在模拟发起一次投递。")
        
        # --- 修改开始: 订阅核心投递流程事件 ---
        # 订阅 'add_friend' 事件，由 ws_client.handle_add_friend 处理，它会调用API发起沟通
        event_manager.subscribe("add_friend", ws_client.handle_add_friend)
        # 订阅 'apply_to_job' 事件，由 ws_client.handle_application 处理，它会在沟通成功后发送问候语
        event_manager.subscribe("apply_to_job", ws_client.handle_application)
        # --- 修改结束 ---

        # 为了验证完整流程，我们监听最终的成功事件
        application_confirmed = asyncio.Event()
        async def confirm_application_sent(job_data, **kwargs):
            logger.info("***** 流程确认: 收到 'application_sent_successfully' 事件! *****")
            application_confirmed.set()

        event_manager.subscribe("application_sent_successfully", confirm_application_sent)

        # 发布 "add_friend" 事件，这是整个投递流程的起点
        logger.info(f"发布 'add_friend' 事件，目标职位: {FIXED_JOB_DATA.get('jobInfo', {}).get('jobName')}")
        await event_manager.publish("add_friend", job_data=FIXED_JOB_DATA, greeting_message="你好，我对这个职位很感兴趣，希望能进一步了解。")

        # 等待最终确认事件，或超时
        try:
            await asyncio.wait_for(application_confirmed.wait(), timeout=30.0)
            logger.info("【测试成功】: 在30秒内确认投递流程已执行完毕。")
        except asyncio.TimeoutError:
            logger.error("【测试失败】: 30秒内未收到投递成功确认事件。")
            logger.error("诊断建议: ")
            logger.error("1. 检查 'zhipin_api.start_chat' 是否成功 (如果失败，不会有后续事件)。")
            logger.error("2. 检查 'ws_client.handle_application' 是否被触发。")
            logger.error("3. 检查 'ws_client._send_greeting_message' 中的消息发送逻辑。")

    # # 等待60s观察，mqtt是否会被服务端关闭
    # await asyncio.sleep(60)

    # --- 5. 清理资源 ---
    logger.info("测试结束，正在关闭所有资源...")
    stop_flag.set()
    await asyncio.sleep(2)  # 等待任务响应停止信号
    await ws_client.close()
    await zhipin_api.close()
    if ws_task:
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass
    logger.info("测试脚本执行完毕。")


if __name__ == "__main__":
    if 'xxxxxxxx' in FIXED_JOB_DATA['securityId']:
        print("="*60)
        print("【运行前必读】")
        print("请打开 `test_ws_client.py` 文件, 修改 `FIXED_JOB_DATA` 字典。")
        print("将其中所有的 'xxxxxxxx' 替换为一个真实、有效且未投递过的岗位ID。")
        print(f"同时，请确保有效的账号cookie文件 '{ACCOUNT_FILE}' 存在。")
        print("="*60)
    else:
        try:
            asyncio.run(run_test())
        except KeyboardInterrupt:
            logger.info("测试被手动中断。")