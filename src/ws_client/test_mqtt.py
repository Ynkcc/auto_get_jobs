from mitmproxy import ctx, http
from mitmproxy.websocket import WebSocketData
import json
import logging
import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from google.protobuf import json_format
from techwolf_pb2 import TechwolfChatProtocol

import sys
from google.protobuf import json_format
from techwolf_pb2 import TechwolfChatProtocol

# 示例测试数据（用户可替换）
# 原始数据：32d401000463...
# 示例为包含MQTT头的Protobuf消息（需替换为实际抓包数据）
data = "32 25 00 04 6368617478700806421708fbf19fa3021084ced6be8ed92a18e8c7dafed63228005001".replace(' ','')
def print_mqtt_info(packet_type, flags, qos, topic, packet_id, payload):
    """打印MQTT报文详细信息"""
    print("\n" + "="*40 + " MQTT协议解析 " + "="*40)
    
    # 报文类型映射表
    type_map = {
        1: "CONNECT", 2: "CONNACK", 3: "PUBLISH", 4: "PUBACK",
        5: "PUBREC", 6: "PUBREL", 7: "PUBCOMP", 8: "SUBSCRIBE",
        9: "SUBACK", 10: "UNSUBSCRIBE", 11: "UNSUBACK",
        12: "PINGREQ", 13: "PINGRESP", 14: "DISCONNECT"
    }
    
    print(f"报文类型: {packet_type} ({type_map.get(packet_type, '未知类型')})")
    print(f"标志位: 0x{flags:02x}")
    
    # QoS说明
    qos_map = {
        0: "最多一次传输 (Fire and Forget)",
        1: "至少一次传输 (Acknowledged delivery)",
        2: "仅一次传输 (Assured delivery)"
    }
    print(f"QoS等级: {qos} - {qos_map.get(qos, '未知等级')}")
    
    print(f"主题名: {topic.decode('utf-8', errors='replace')}")
    if qos > 0:
        print(f"报文标识符: {packet_id} (用于消息确认机制)")
    print(f"有效载荷长度: {len(payload)} bytes")

def parse_mqtt(data: bytes):

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



    payload= data[index:]
    return {
        "packet_type": packet_type,
        "flags": None,
        "qos": qos,
        "topic": topic,
        "packet_id": packet_id,
        "payload": payload
    }

def parse_protobuf(data: bytes) -> dict:
    """Protobuf解析（带详细字段说明）"""
    try:
        protocol = TechwolfChatProtocol()
        protocol.ParseFromString(data)
        result = json_format.MessageToDict(
            protocol
        )

        return result
    except Exception as e:
        raise ValueError(f"Protobuf解析失败: {str(e)}")

def hex_to_bytes(hex_str: str) -> bytes:
    """十六进制字符串转bytes（带校验）"""
    hex_str = hex_str.strip().lower()
    if not all(c in '0123456789abcdef' for c in hex_str):
        raise ValueError("包含非法字符，必须为0-9,a-f")
    
    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制长度必须为偶数")
        
    return bytes.fromhex(hex_str)

def main():
    # 用户输入处理
    if not data:
        print("请先设置data变量的值")
        return

    try:
        raw_data = hex_to_bytes(data)
    except ValueError as e:
        print(f"数据转换错误: {str(e)}")
        return


    # 尝试MQTT+Protobuf解析
    mqtt_result = parse_mqtt(raw_data)
    print_mqtt_info(**mqtt_result)
    
    print("\n" + "="*40 + " Protobuf解析 " + "="*40)
    proto_result = parse_protobuf(mqtt_result["payload"])
    print(json.dumps(proto_result, indent=2, ensure_ascii=False))
        

if __name__ == "__main__":
    main()
