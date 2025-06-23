# src/services/ws_client/client.py
import asyncio
import logging
import time
import ssl
from typing import Dict
import paho.mqtt.client as mqtt

from ...common.config_manager import ConfigManager
from ...common.event_manager import event_manager
from ...common.file_utils import calculate_md5
from ..ai_analyzer import AiAnalyzer
from ..zhipin_api import zhipin_api
from . import techwolf_pb2
from .patched_mqtt import patch_client

logger = logging.getLogger(__name__)

class WsClient:
    def __init__(self, config: ConfigManager, stop_flag: asyncio.Event):
        self.config = config
        self.ws_config = config.ws_client
        self.app_config = config.application
        self.ai_analyzer = AiAnalyzer()
        self.stop_flag = stop_flag
        
        self.client: patch_client = None
        self.user_id: int = None
        self.wt2: str = None
        
        self.is_connected = False
        self.resume_image_md5 = None
        self._prepare_resume_image()

    def _prepare_resume_image(self):
        """准备简历图片，计算MD5"""
        if self.app_config.send_resume_image:
            image_path = self.app_config.resume_image_file
            try:
                self.resume_image_md5 = calculate_md5(image_path)
                logger.info(f"已计算简历图片MD5: {self.resume_image_md5}")
            except FileNotFoundError:
                logger.error(f"简历图片文件未找到: {image_path}，将无法发送图片。")
                self.app_config.send_resume_image = False
            except Exception as e:
                logger.error(f"准备简历图片时发生错误: {e}")
                self.app_config.send_resume_image = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("WebSocket (MQTT) 连接成功")
            self.is_connected = True
            client.subscribe(f"r/u/g/{self.user_id}", qos=1)
        else:
            logger.error(f"WebSocket (MQTT) 连接失败，返回码: {rc}")
            self.is_connected = False

    def _on_message(self, client, userdata, msg):
        try:
            protocol = techwolf_pb2.TechwolfChatProtocol()
            protocol.ParseFromString(msg.payload)
            logger.debug(f"收到消息: {protocol}")
        except Exception as e:
            logger.error(f"处理接收到的消息时出错: {e}", exc_info=True)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        logger.warning(f"WebSocket (MQTT) 连接已断开，返回码: {rc}")
        self.is_connected = False

    def _init_client(self):
        """初始化并配置MQTT客户端"""
        client_id = f"w_{self.user_id}_{int(time.time() * 1000)}"
        self.client = patch_client(
            client_id=client_id,
            transport="websockets",
            protocol=mqtt.MQTTv5
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.client.tls_set(ssl.CERT_NONE)
        self.client.ws_options_set(path="/ws-v2", headers={"X-CLIENT-ID": client_id})
        self.client.username_pw_set(str(self.user_id), self.wt2)

    async def _send_greeting_message(self, to_uid: str, job_data: dict):
        """发送文本打招呼语和简历图片"""
        job_info = job_data.get("jobInfo", {})
        brand_info = job_data.get("brandComInfo", {})
        job_name = job_info.get("jobName", "这个职位")
        company = brand_info.get("brandName", "贵公司")
        
        greeting_text = self.app_config.greeting.greeting_prompt.format(job_name=job_name, company=company)
        
        logger.info(f"已向 {to_uid} 发送招呼语: {greeting_text} (模拟发送)")

        if self.app_config.send_resume_image and self.resume_image_md5:
            image_path = self.app_config.resume_image_file
            # securityId 在顶层
            security_id = job_data.get('securityId')
            image_result = await zhipin_api.upload_image(image_path, security_id, self.resume_image_md5)
            if image_result:
                logger.info(f"已向 {to_uid} 发送简历图片 (模拟发送)")
            else:
                logger.error(f"上传简历图片失败，无法发送给 {to_uid}")

    async def run(self):
        """主运行循环，负责保持WebSocket连接"""
        await zhipin_api.get_user_info()
        self.user_id = zhipin_api.get_user_id()
        self.wt2 = await zhipin_api.get_wt2()
        
        if not self.user_id or not self.wt2:
            logger.error("无法获取用户信息或wt2，WsClient无法启动")
            return

        self._init_client()
        logger.info("正在连接 WebSocket (MQTT)...")
        self.client.connect(self.ws_config.host, self.ws_config.port, 60)
        self.client.loop_start()

        try:
            await self.stop_flag.wait()
        finally:
            if self.client:
                self.client.loop_stop()
            logger.info("WebSocket客户端循环已停止")

    async def handle_add_friend(self, job_data: dict, **kwargs):
        """事件订阅函数：处理添加好友请求 (实际是发起沟通)"""
        if not self.is_connected:
            logger.warning("WebSocket未连接，无法发起沟通")
            return
        
        job_info = job_data.get('jobInfo', {})
        job_name = job_info.get('jobName')
        security_id = job_data.get('securityId') # securityId 在顶层
        
        logger.info(f"WsClient 收到任务，准备与 '{job_name}' 的HR发起沟通")

        try:
            encrypt_job_id = job_info.get('encryptId')
            lid = job_data.get('lid')

            if not all([encrypt_job_id, security_id, lid]):
                logger.error("缺少必要参数 (encryptJobId, securityId, lid)，无法发起沟通")
                return

            result = await zhipin_api.start_chat(security_id, encrypt_job_id, lid)

            if result and result.get('code') == 0:
                logger.info(f"成功与 '{job_name}' 的HR建立沟通")
                await event_manager.publish("apply_to_job", job_data=job_data)
            else:
                message = result.get('message', '未知错误') if result else "请求失败"
                logger.warning(f"与 '{job_name}' 的HR建立沟通失败: {message}")

        except Exception as e:
            logger.error(f"发起沟通时发生异常: {e}", exc_info=True)
            
    async def handle_application(self, job_data: dict, **kwargs):
        """事件订阅函数：处理投递申请（发送招呼语和简历）"""
        if not self.is_connected:
            logger.warning("WebSocket未连接，无法发送招呼语")
            return

        boss_info = job_data.get("bossInfo", {})
        encrypt_geek_id = boss_info.get("encryptUserId")
        
        if not encrypt_geek_id:
            logger.error("职位数据中未找到对方ID (encryptUserId)，无法发送消息")
            return

        try:
            await self._send_greeting_message(encrypt_geek_id, job_data)
            await event_manager.publish("application_sent_successfully", job_data=job_data)
        except Exception as e:
            logger.error(f"处理投递申请时发生异常: {e}", exc_info=True)

    async def close(self, **kwargs):
        if self.is_connected and self.client:
            self.client.disconnect()
        logger.info("WsClient 已关闭")