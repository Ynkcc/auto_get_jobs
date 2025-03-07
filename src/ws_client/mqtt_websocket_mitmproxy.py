from mitmproxy import ctx, http
from mitmproxy.websocket import WebSocketData
import json
import logging
import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from google.protobuf import json_format
from techwolf_pb2 import TechwolfChatProtocol

class BossZPInspector:
    """
    Boss直聘WebSocket分析工具
    """
    
    def __init__(self):
        self.target_host = "ws6.zhipin.com"
        self.connection_map = {}
        self._configure_logger()

    def _configure_logger(self):
        """自定义日志配置"""
        self.logger = logging.getLogger("BOSS_WS_FILE_LOGGER")
        self.logger.setLevel(logging.DEBUG)

        # 清除可能存在的默认handler
        if self.logger.handlers:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)

        # 创建轮转日志handler
        handler = RotatingFileHandler(
            filename='boss_websocket.log',
            mode='a',
            maxBytes=1*1024*1024,  # 100MB
            backupCount=0,
            encoding='utf-8'
        )

        # 设置日志格式
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def websocket_message(self, flow: http.HTTPFlow) -> None:
        """处理WebSocket消息"""
        if flow.request.host != self.target_host:
            return

        message = flow.websocket.messages[-1]
        
        try:
            metadata = {
                "client": flow.client_conn.peername[0],
                "direction": "C→S" if message.from_client else "S→C",
                "type": "TEXT" if message.is_text else "BIN",
                "size": f"{len(message.content):,}b",
                "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            }

            log_entry = {
                "meta": metadata,
                "content": self._parse_content(message)
            }

            self.logger.info("\n" + json.dumps(
                log_entry, 
                indent=2, 
                ensure_ascii=False,
                sort_keys=False
            ))

        except Exception as e:
            self.logger.error(f"PROCESS ERROR: {str(e)}", exc_info=True)

    def _parse_content(self, message) -> Optional[dict]:
        """解析消息内容"""
        if message.is_text:
            return {"text": message.content}
        
        content = message.content if isinstance(message.content, bytes) else message.content.encode()
        
        # 尝试MQTT+Protobuf解析
        try:
            mqtt_payload = self._parse_mqtt(content)
            return self._parse_protobuf(mqtt_payload)
        except Exception as e:
            self.logger.debug(f"解析失败，输出原始hex: {str(e)}")
            return {"raw_hex": content.hex()}

    def _parse_protobuf(self, data: bytes) -> dict:
        """Protobuf解析统一方法"""
        protocol = TechwolfChatProtocol()
        protocol.ParseFromString(data)
        return json_format.MessageToDict(
            protocol
        )

    def _parse_mqtt(self, data: bytes) -> bytes:

        first_byte = data[0]
        packet_type = (first_byte & 0xF0) >> 4
        qos_flag = first_byte & 0b00000110

        # 仅处理PUBLISH报文（类型3）
        if packet_type != 3:
            raise ValueError(f"非PUBLISH类型MQTT报文: {packet_type}")

        # 解析剩余长度
        index = 1
        while data[index]>0x7f and index<=4:
            index+=1

        index +=1

        topic_name_length=int.from_bytes(data[index:index+2], byteorder='big')
        index+=2
        index+=topic_name_length


        if qos_flag > 0:
            index += 2

        return data[index:]

addons = [BossZPInspector()]
