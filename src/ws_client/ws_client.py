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
class WSclient(threading.Thread):
    hostname = "ws6.zhipin.com"
    port = 443
    topic = '/chatws'
    reconnect_interval = 10  # 重连间隔秒数
    uid = None
    token = None
    wt2 = None

    def __init__(self, recv_queue, running_event, image_dict=None, headers=None, cookies=None, logger=None):
        """
        初始化WebSocket客户端
        :param recv_queue: 接收任务队列(Queue类型)
        :param headers: 请求头字典
        :param cookies: cookies字典
        """
        super().__init__(daemon=True)
        self.recv_queue = recv_queue
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.logger = logger or logging.getLogger(__name__)
        self.image_dict = image_dict
        client_id = f"ws-{secrets.token_hex(8).upper()}"
        # MQTT客户端配置
        self.client = mqtt.Client(
            client_id=client_id,
            protocol=3,
            transport='websockets',
            clean_session=True
        )
        self._setup_callbacks()
        self._running = running_event

    def _setup_callbacks(self):
        """配置回调函数"""
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self.logger.info("WebSocket connected successfully")
            client.subscribe(self.topic)
        else:
            self.logger.error(f"Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """连接断开回调"""
        self.logger.warning(f"Disconnected with code {rc}")
        if self._running.is_set():
            self._reconnect()

    def _on_message(self, client, userdata, msg):
        """消息接收处理"""
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
        """协议消息分发处理"""
        msg_type = data.get('type')
        handler = {
            1: self._handle_chat_message,
            4: self._handle_suggest_message,
            6: self._handle_sync_message,
            7: self._handle_resume_request
        }.get(msg_type, lambda x: None)
        handler(data)

    def _handle_chat_message(self, data):
        """处理聊天消息"""
        message = data['messages'][-1]
        body = message['body']
        if body['type'] == 1:
            self.on_text_message(
                from_uid=message['from']['uid'],
                text=body['text'],
                timestamp=message['time']
            )

    def _handle_resume_request(self, data):
        """处理简历请求"""
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
        """实现自动重连机制"""
        while self._running.is_set():
            try:
                self.logger.info("Attempting to reconnect...")
                self.client.reconnect()
                return
            except Exception as e:
                self.logger.error(f"Reconnect failed: {str(e)}")
                time.sleep(self.reconnect_interval)

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
            mid = int(time.time() * 1000)
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
                        "time": int(time.time() * 1000),
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
        self.uid, self.token = self.get_userinfo()
        self.wt2 = self.get_wt2()

        # 配置WebSocket连接
        ws_headers = {
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "User-Agent": self.headers.get('User-Agent', '')
        }

        self.client.ws_set_options(
            path=self.topic,
            headers=ws_headers
        )
        self.client.tls_set()
        self.client.enable_logger(logger=logger)
        self.client.username_pw_set(self.token + "|0", self.wt2)

        # 建立连接
        self.client.connect(self.hostname, self.port, keepalive=15)
        self.client.loop_start()
        self._running.set()
        # 任务处理循环
        while self._running.is_set():
            try:
                task = self.recv_queue.get(timeout=1)
                if task:
                    self.send_message(task)
                    time.sleep(2)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Task processing error: {str(e)}")
        self.stop()

    def stop(self):
        """安全停止客户端"""
        self._running.clear()
        self.client.disconnect()
        self.client.loop_stop()

    def get_userinfo(self):
        """获取用户身份信息"""
        try:
            url = "https://www.zhipin.com/wapi/zpuser/wap/getUserInfo.json"
            response = requests.get(
                url,
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            user_info = response.json()

            if user_info['code'] == 0:
                zp_data = user_info['zpData']
                return (
                    zp_data.get('userId'),
                    zp_data.get('token')
                )
            raise Exception(f"获取用户信息失败: {user_info.get('message')}")
        except Exception as e:
            self.logger.error(f"获取用户信息异常: {str(e)}")
            return None, None

    def get_wt2(self):
        """获取wt2验证参数"""
        try:
            url = "https://www.zhipin.com/wapi/zppassport/get/wt"
            response = requests.get(
                url,
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            wt2_data = response.json()

            if wt2_data['code'] == 0:
                return wt2_data['zpData'].get('wt2')
            raise Exception(f"获取wt2失败: {wt2_data.get('message')}")
        except Exception as e:
            self.logger.error(f"获取wt2异常: {str(e)}")
            return None

    def get_boss_data(self, encryptBossId):
        try:
            baseurl = "https://www.zhipin.com"
            path = '/wapi/zpchat/geek/getBossData'
            url = baseurl + path
            params = {
                "bossId": encryptBossId,
                "bossSource": 0
            }
            response = requests.get(
                url,
                params=params,
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            boss_info = response.json()

            if boss_info['code'] == 0:
                zp_data = boss_info['zpData']["data"]
                return (zp_data.get('bossId'), boss_info)
        except Exception as e:
            return None

    # 以下为需要外部实现的回调接口
    def on_text_message(self, from_uid, text, timestamp):
        """收到文字消息回调（需子类实现）"""
        pass

    def on_request_resume(self, boss_id, mid):
        """收到简历请求回调（需子类实现）"""
        pass

    def on_application_result(self, job_id, result):
        """职位申请结果回调（需子类实现）"""
        pass

if __name__ == "__main__":
    # 测试用参数
    test_queue = queue.Queue()
    test_event = threading.Event()
    test_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
    with open("data/account1.json", "r", encoding="utf8") as f:
        cookies = json.load(f)["cookies"]
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    test_logger = logging.getLogger("ws_client")
    test_logger.setLevel(logging.DEBUG)  # 设置最低记录级别

    # 创建 Handler（控制台 + 文件）
    console_handler = logging.StreamHandler()

    # 设置 Handler 级别
    console_handler.setLevel(logging.DEBUG)  # 控制台只记录 WARNING 及以上

    # 定义日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # 将 Handler 添加到 Logger
    test_logger.addHandler(console_handler)
    image_dict = {
        "url": "https://img.bosszhipin.com/beijin/upload/tmp/20250305/8f00b204e98009986ff8e7a2df03c5c14b1b103c92129ecfd6fdbaaac6966d6a8ef5e5092165499b.png",
        "width": 1700,
        "height": 2200
    }
    client = WSclient(
        recv_queue=test_queue,
        running_event=test_event,
        image_dict=image_dict,
        headers=test_headers,
        cookies=cookies_dict,
        logger=test_logger
    )

    test_event.set()
    client.start()
    test_queue.put(("image", "3aa60c387c96fc671X172d66GFM~", ""))
    input("按下任意键，退出")