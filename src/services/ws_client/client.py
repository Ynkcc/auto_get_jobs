# src/services/ws_client/client.py

import asyncio
import logging
import time
import ssl
import json
import secrets
from typing import Dict
import paho.mqtt.client as mqtt
from paho.mqtt.enums import MessageType
from google.protobuf import json_format

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
        self.user_token: str = None # token 即 mqtt的用户名
        self.user_id: int = None # 用户ID
        self.wt2: str = None

        # 用于存储会话信息，由事件更新
        self.headers: dict = {}
        self.cookies: dict = {}

        self.is_connected = False
        self.resume_image_md5 = None
        self._prepare_resume_image()

        self.sent_count = 0
        self.success_count = 0
        self.reconnect_interval = 8 # 秒
        # 获取并存储当前的事件循环，用于线程安全的回调
        self.loop = asyncio.get_running_loop()

        # 【新增】增加一个状态标志，防止重复关闭
        self._is_closing = False


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

    async def _handle_cookies_updated(self, cookies_data: dict, **kwargs):
        """事件订阅函数：处理 cookies 更新，并触发重连以应用新凭据"""
        logger.info("WsClient 收到 cookies_updated 事件，正在更新会话信息并准备重连...")

        self.headers = cookies_data.get("headers", {})
        cookies_list = cookies_data.get("cookies", [])
        self.cookies = {c['name']: c['value'] for c in cookies_list}

        try:
            self.wt2 = await zhipin_api.get_wt2()
            if self.wt2:
                logger.info("wt2 凭据已刷新。")
            else:
                logger.error("刷新 wt2 凭据失败，可能导致重连失败。")

        except Exception as e:
            logger.error(f"处理 cookies 更新事件时发生错误: {e}", exc_info=True)


    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("WebSocket (MQTT) 连接成功")
            self.is_connected = True
            topic = "chat"
            client.subscribe(topic, qos=1)
            logger.info(f"已订阅主题: {topic}")
        else:
            logger.error(f"WebSocket (MQTT) 连接失败，返回码: {rc}。请检查网络或凭据。")
            self.is_connected = False

    def _on_publish(self, client, userdata, mid):
        self.success_count += 1
        logger.debug(f"消息发布成功 (mid: {mid}), 成功数: {self.success_count}, 已发送数: {self.sent_count}")


    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"WebSocket (MQTT) 连接已断开，返回码: {rc}")
        self.is_connected = False
        if not self.stop_flag.is_set():
            logger.info(f"将在 {self.reconnect_interval} 秒后尝试重连...")
            asyncio.run_coroutine_threadsafe(self._reconnect(), self.loop)

    async def _reconnect(self):
        """异步重连逻辑"""
        await asyncio.sleep(self.reconnect_interval)
        logger.info("正在尝试重连...")
        try:
            self.wt2 = await zhipin_api.get_wt2()
            if not self.wt2:
                 logger.error("刷新 wt2 凭据失败，无法重连")
                 return

            self.client.username_pw_set(f"{self.user_token}|0", self.wt2)

            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            client_id = self.client._client_id.decode('utf-8') if self.client._client_id else f"w_{self.user_id}_{int(time.time() * 1000)}"
            ws_headers = {
                "X-CLIENT-ID": client_id,
                "User-Agent": self.headers.get('User-Agent', ''),
                "Cookie": cookie_str,
                "Sec-WebSocket-Protocol": self.wt2,
            }

            if hasattr(self.client, 'ws_set_options'):
                self.client.ws_set_options(path="/chatws", headers=ws_headers)
            else:
                self.client.ws_options_set(path="/chatws", headers=ws_headers)

            self.client.reconnect()
        except Exception as e:
            logger.error(f"重连过程中发生严重错误: {e}", exc_info=True)


    def _on_message(self, client, userdata, msg):
        try:
            protocol = techwolf_pb2.TechwolfChatProtocol()
            protocol.ParseFromString(msg.payload)
            data = json_format.MessageToDict(protocol, preserving_proto_field_name=True)

            logger.debug(f"收到已解析消息: {json.dumps(data, indent=2, ensure_ascii=False)}")
            asyncio.run_coroutine_threadsafe(self._handle_protocol_message(data), self.loop)
        except Exception as e:
            logger.error(f"处理接收到的消息时出错: {e}", exc_info=True)

    async def _handle_protocol_message(self, data: dict):
        msg_type = data.get('type')
        if msg_type == 1:
            await self._handle_chat_message(data)
        elif msg_type == 4:
            await self._handle_suggest_message(data)
        elif msg_type == 6:
            await self._handle_sync_message(data)
        elif msg_type == 7:
            await self._handle_resume_request(data)
        else:
            logger.debug(f"收到未知的消息类型: {msg_type}，暂不处理。")

    async def _handle_chat_message(self, data: dict):
        if not data.get('messages'): return
        message = data['messages'][-1]
        body = message.get('body', {})
        if body.get('type') == 1:
            from_uid = message.get('from', {}).get('uid')
            text = body.get('text')
            timestamp = message.get('time')
            logger.info(f"收到来自 {from_uid} 的文本消息: {text}")
            await event_manager.publish("new_text_message", from_uid=from_uid, text=text, timestamp=timestamp)

    async def _handle_resume_request(self, data: dict):
        if not data.get('messages'): return
        message = data['messages'][-1]
        from_info = message.get('from', {})
        if from_info.get('uid') != self.user_id:
            boss_id = from_info.get('uid')
            mid = message.get('mid')
            logger.info(f"HR {boss_id} 正在索要您的简历。")
            await event_manager.publish("resume_requested", boss_id=boss_id, mid=mid)

    async def _handle_suggest_message(self, data: dict):
        logger.debug("收到建议性消息，当前版本不作处理。")
        pass

    async def _handle_sync_message(self, data: dict):
        logger.debug("收到同步消息，当前版本不作处理。")
        pass

    def _init_client(self):
        """初始化并配置MQTT客户端"""
        client_id = f"ws-{secrets.token_hex(8).upper()}"
        self.client = patch_client(client_id=client_id, transport="websockets")

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        self.client.tls_set()
        self.client.tls_insecure_set(False)

        cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
        ws_headers = {
            "X-CLIENT-ID": client_id,
            "User-Agent": self.headers.get('User-Agent', ''),
            "Cookie": cookie_str,
            "Sec-WebSocket-Protocol": self.wt2
        }

        if hasattr(self.client, 'ws_set_options'):
             self.client.ws_set_options(path="/chatws", headers=ws_headers)
        else:
             self.client.ws_options_set(path="/chatws", headers=ws_headers)

        auth_username = f"{self.user_token}|0"
        self.client.username_pw_set(auth_username, self.wt2)

    def _publish_proto_message(self, to_uid: str, msg_body: dict):
        """构建并直接发布Protobuf消息。"""
        if not self.is_connected:
            logger.warning("WebSocket未连接，消息已由paho-mqtt客户端排队。")

        timestamp = int(time.time() * 1000)
        chat_dict = {"type": 1, "messages": [{"from": {"uid": "0"}, "to": {"uid": "0", "name": to_uid}, "type": 1, "mid": timestamp, "time": timestamp, "body": msg_body, "cmid": timestamp}]}

        try:
            protocol = techwolf_pb2.TechwolfChatProtocol()
            json_format.ParseDict(chat_dict, protocol)
            payload = protocol.SerializeToString()

            # 直接发布，paho-mqtt会处理排队和重试
            self.client.publish('chat', payload, qos=1)
            self.sent_count += 1
            logger.debug(f"已向主题 'chat' 发布消息至 {to_uid}")

        except Exception as e:
            logger.error(f"构建或发布Protobuf消息时出错: {e}", exc_info=True)

    async def _send_greeting_message(self, to_uid: str, greeting_text: str, job_data: dict):
        """发送文本打招呼语和简历图片"""
        self._publish_proto_message(to_uid, {"templateId": 1, "text": greeting_text, "type": 1})
        logger.info(f"已向 {to_uid} 发送招呼语: {greeting_text}")

        if self.app_config.send_resume_image and self.resume_image_md5:
            await asyncio.sleep(0.5)
            image_path, security_id = self.app_config.resume_image_file, job_data.get('securityId')
            image_result = await zhipin_api.upload_image(image_path, security_id, self.resume_image_md5)
            if image_result:
                self._publish_proto_message(to_uid, {"templateId": 1, "type": 3, "image": image_result})
                logger.info(f"已向 {to_uid} 发送简历图片")
            else:
                logger.error(f"上传简历图片失败，无法发送给 {to_uid}")

    async def run(self):
        """主运行循环，负责保持WebSocket连接"""
        logger.info("WsClient 已启动，正在等待 API 客户端就绪...")
        # 订阅事件已移至 main.py

        await zhipin_api.wait_for_ready()

        self.wt2 = await zhipin_api.get_wt2()
        self.user_token = zhipin_api.get_user_token()
        self.user_id = zhipin_api.get_user_id()

        if not all([self.user_token, self.wt2, self.headers, self.cookies]):
            logger.error("无法获取启动 WsClient 所需的完整凭据。客户端将保持非活动状态。")
            await self.stop_flag.wait()
            return

        logger.info("API客户端已就绪，WsClient开始初始化连接...")
        self._init_client()

        try:
            self.client.connect(self.ws_config.host, self.ws_config.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"连接到 WebSocket 服务器失败: {e}。程序将等待停止信号。")
            await self.stop_flag.wait()
            return

        try:
            await self.stop_flag.wait()
        finally:
            logger.info("收到停止信号，开始优雅关闭 WsClient...")
            await self.close()
            if self.client and self.client.is_connected():
                self.client.loop_stop()
            logger.info("WsClient 已完全停止")


    async def handle_add_friend(self, job_data: dict, greeting_message: str, **kwargs):
        if not self.is_connected:
            logger.warning("WebSocket未连接，无法发起沟通")
            return
        job_info = job_data.get('jobInfo', {})
        job_name, security_id = job_info.get('jobName'), job_data.get('securityId')
        logger.info(f"WsClient 收到任务，准备与 '{job_name}' 的HR发起沟通")

        try:
            encrypt_job_id, lid = job_info.get('encryptId'), job_data.get('lid')
            if not all([encrypt_job_id, security_id, lid]):
                logger.error("缺少必要参数 (encryptJobId, securityId, lid)，无法发起沟通")
                return
            result = await zhipin_api.start_chat(security_id, encrypt_job_id, lid)
            if result and result.get('code') == 0:
                logger.info(f"成功与 '{job_name}' 的HR建立沟通")
                job_data["bossInfo"]['encBossId'] = result.get('zpData', {}).get('encBossId')
                await event_manager.publish("apply_to_job", job_data=job_data, greeting_message=greeting_message)
            else:
                message = result.get('message', '未知错误') if result else "请求失败"
                logger.warning(f"与 '{job_name}' 的HR建立沟通失败: {message}")
        except Exception as e:
            logger.error(f"发起沟通时发生异常: {e}", exc_info=True)

    async def handle_application(self, job_data: dict, greeting_message: str, **kwargs):
        if not self.is_connected and not self.client:
             logger.warning("客户端未初始化，无法发送招呼语")
             return

        encrypt_geek_id = job_data.get("bossInfo", {}).get("encBossId")
        if not encrypt_geek_id:
            logger.error("职位数据中未找到对方ID (encBossId)，无法发送消息")
            return

        greeting = greeting_message
        if not greeting:
            greeting = "你好，我对这个职位感兴趣，希望能进一步了解。"
            logger.warning("未提供招呼语，使用默认招呼语: " + greeting)

        try:
            await self._send_greeting_message(encrypt_geek_id, greeting, job_data)
            await event_manager.publish("application_sent_successfully", job_data=job_data)
        except Exception as e:
            logger.error(f"处理投递申请时发生异常: {e}", exc_info=True)

    async def close(self, timeout=10):
        """
        【修改】优雅地断开连接，等待所有消息发送和确认。
        通过状态标志防止重复执行。
        """
        # 【修改】如果正在关闭，则直接返回，防止重复执行
        if self._is_closing:
            logger.info("关闭流程已在进行中，跳过重复请求。")
            return
        self._is_closing = True

        if not self.client:
            logger.info("客户端未初始化，无需断开。")
            return

        logger.info("开始优雅断开流程...")

        # 等待消息队列清空
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 【修改】修正队列大小的获取方式
            # _out_messages 是一个类字典，需要用 len()
            # _inflight_messages 是一个整数，直接使用
            out_queue_size = len(self.client._out_messages) if hasattr(self.client, '_out_messages') else 0
            inflight_queue_size = self.client._inflight_messages if hasattr(self.client, '_inflight_messages') else 0

            if out_queue_size == 0 and inflight_queue_size == 0:
                logger.info("所有待处理消息已发送和确认。")
                break

            logger.info(f"等待消息队列清空... 待发送: {out_queue_size}, 待确认: {inflight_queue_size}")
            await asyncio.sleep(0.5)
        else:
            logger.warning(f"优雅断开超时（{timeout}秒），可能仍有未处理的消息。")

        self.client.disconnect()
        logger.info("已向MQTT代理发送断开连接请求。")