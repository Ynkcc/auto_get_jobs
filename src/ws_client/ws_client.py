'''
original code from https://github.com/xmiaoq/bossbot
EditBy : Ynkcc
'''
import logging
logger = logging.getLogger(__name__)
import threading
import time
import json
import queue
import requests
import paho.mqtt.client as mqtt
from .techwolf_pb2 import TechwolfChatProtocol
from google.protobuf import json_format
import secrets
from utils.general import get_user_info,get_wt2

class WsClient(threading.Thread):
    hostname = "ws6.zhipin.com"
    port = 443
    path = '/chatws'
    topic = 'chat'
    reconnect_interval = 10  # 重连间隔秒数
    uid = None
    token = None
    wt2 = None

    def __init__(self, recv_queue, done_event, running_event):
        """
        初始化WebSocket客户端
        :param recv_queue: 接收任务队列(Queue类型)
        :param headers: 请求头字典
        :param cookies: cookies字典
        """
        super().__init__(daemon=True)
        self.recv_queue = recv_queue
        self.headers = None
        self.cookies = None
        self.logger = logger or logging.getLogger(__name__)
        self.image_dict = None
        self.client = None
        self.done = done_event
        self._running = running_event

    def _init_client(self):
        client_id = f"ws-{secrets.token_hex(8).upper()}"
        # MQTT客户端配置
        self.client = mqtt.Client(
            client_id=client_id,
            protocol=3,
            transport='websockets',
            clean_session=True
        )
        self._setup_callbacks()
        self.uid, user_info = get_user_info(self.cookies,self.headers)
        self.token = user_info["zpData"]['token']
        self.wt2 = get_wt2(self.cookies,self.headers)

        # 配置WebSocket连接
        ws_headers = {
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "User-Agent": self.headers.get('User-Agent', '')
        }

        self.client.ws_set_options(
            path=self.path,
            headers=ws_headers
        )
        self.client.tls_set()
        self.client.enable_logger(logger=logger)
        self.client.username_pw_set(self.token + "|0", self.wt2)

        # 建立连接
        self.client.connect(self.hostname, self.port, keepalive=15)
        self.client.loop_start()

    def send_message(self, task):
        """
        发送文本消息
        :param boss_id: 对方boss_id
        :param msg: 消息内容
        :return:
        """
        msgtype, boss_id, msg = task
        try:
            protocol = TechwolfChatProtocol()
            t = int(time.time() * 1000)
            mid = t + 68256432452609
            chat = {
                "type": 1,
                "messages": [
                    {
                        "from": {
                            "uid": "0"
                        },
                        "to": {
                            "uid": "0",
                            "name": boss_id
                        },
                        "type": 1,
                        "mid": mid,
                        "time": t,
                        "body": {
                            "templateId": 1,
                        },
                        "cmid": mid
                    }
                ]
            }
            if msgtype == "msg":
                chat["messages"][0]["body"]["text"] = msg
                chat["messages"][0]["body"]["type"] = 1
            elif msgtype == "image":
                chat["messages"][0]["body"]["type"] = 3
                chat["messages"][0]["body"]["image"] = {"originImage": self.image_dict}
            else:
                return
            json_format.ParseDict(chat, protocol)
            self.client.publish(self.topic, protocol.SerializeToString())
        except Exception as e:
            self.logger.error(f"Failed to send application: {str(e)}")

    def run(self):
        """主运行循环"""
        while self._running.is_set():
            recv_msg = self.recv_queue.get()
            if recv_msg[0]=="update_cookies":
                _, self.cookies, self.headers = recv_msg
                if self.client is None:
                    self._init_client()
            elif recv_msg[0]=="task":
                if self.client is None:
                    self.recv_queue.put(recv_msg)
                _, task = recv_msg
                self.done.clear()
                self.send_message(task)
                self.done.set()
        self.stop()

    def stop(self):
        """安全停止客户端"""
        self._running.clear()
        self.client.disconnect()
        self.client.loop_stop()

    def _setup_callbacks(self):
        """配置回调函数"""
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("WebSocket connected successfully")
            client.subscribe(self.topic)
        else:
            self.logger.error(f"Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.logger.warning(f"Disconnected with code {rc}")
        if self._running.is_set():
            self._reconnect()

    def _on_message(self, client, userdata, msg):
        self.logger.debug("receive message")
        try:
            protocol = TechwolfChatProtocol()
            protocol.ParseFromString(msg.payload)
            data = json_format.MessageToDict(protocol)
            self.logger.debug(json.dumps(data, indent=4, ensure_ascii=False))
            self._handle_protocol_message(data)
        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")

    def _handle_protocol_message(self, data):
        msg_type = data.get('type')
        handler = {
            1: self._handle_chat_message,
            4: self._handle_suggest_message,
            6: self._handle_sync_message,
            7: self._handle_resume_request
        }.get(msg_type, lambda x: None)
        handler(data)

    def _handle_chat_message(self, data):
        message = data['messages'][-1]
        body = message['body']
        if body['type'] == 1:
            self.on_text_message(
                from_uid=message['from']['uid'],
                text=body['text'],
                timestamp=message['time']
            )

    def _handle_resume_request(self, data):
        message = data['messages'][-1]
        if message['from']['uid'] != self.uid:
            self.on_request_resume(
                boss_id=message['from']['uid'],
                mid=message['mid']
            )

    def _handle_suggest_message(self, data):
        pass

    def _handle_sync_message(self, data):
        pass

    def _reconnect(self):
        while self._running.is_set():
            try:
                self.logger.info("Attempting to reconnect...")
                self.client.reconnect()
                return
            except Exception as e:
                #TODO 更新token继续重连
                self.logger.error(f"Reconnect failed: {str(e)}")
                time.sleep(self.reconnect_interval)

    def on_text_message(self, from_uid, text, timestamp):
        pass

    def on_request_resume(self, boss_id, mid):
        pass

    def on_application_result(self, job_id, result):
        pass
