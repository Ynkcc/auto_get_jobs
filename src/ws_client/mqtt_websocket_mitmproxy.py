from mitmproxy import ctx, http
from mitmproxy.websocket import WebSocketData
import json
import logging
import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from google.protobuf import json_format
from techwolf_pb2 import TechwolfChatProtocol
from google.protobuf import json_format

class BossZPInspector:
    """直聘协议解析器（假设数据可靠版本）"""
    
    def __init__(self):
        self.target_host = "ws6.zhipin.com"
        self.logger = self._init_logger()

    def _init_logger(self):
        """初始化日志系统"""
        logger = logging.getLogger("BOSS_WS_LOGGER")
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler('boss_websocket.log', maxBytes=100*1024*1024, backupCount=1, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
        return logger

    def websocket_message(self, flow: http.HTTPFlow) -> None:
        """消息处理入口"""
        if flow.request.host != self.target_host:
            return

        message = flow.websocket.messages[-1]
        metadata = {
            "client": flow.client_conn.peername[0],
            "direction": "C→S" if message.from_client else "S→C",
            "type": "TEXT" if message.is_text else "BIN",
            "size": f"{len(message.content):,}b",
            "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "topic": None
        }
        
        if message.is_text:
            content = {"text": message.content}
        else:
            content, metadata["topic"] = self._parse_binary(message.content)
        if metadata["topic"] is None:
            self.logger.debug("\n%s", json.dumps({"meta": metadata, "content": content}, indent=2, ensure_ascii=False))
        else:
            self.logger.info("\n%s", json.dumps({"meta": metadata, "content": content}, indent=2, ensure_ascii=False))

    def _parse_binary(self, data: bytes) -> tuple:
        """二进制数据统一处理"""
        packet_type = (data[0] & 0xF0) >> 4
        
        if packet_type != 3:  # 非PUBLISH类型
            return {"hex": data.hex()}, None
        
        # MQTT PUBLISH解析
        index = 1
        while data[index] > 0x7f and index <=4:
            index +=1
        index +=1
        
        topic_length = int.from_bytes(data[index:index+2], 'big')
        index +=2
        topic = data[index:index+topic_length].decode()
        index += topic_length
        
        if data[0] & 0x06:  # QoS处理
            index +=2
        
        # Protobuf解析（数据可靠直接解析）
        pb_data = TechwolfChatProtocol()
        pb_data.ParseFromString(data[index:])
        return json_format.MessageToDict(pb_data), topic

addons = [BossZPInspector()]
