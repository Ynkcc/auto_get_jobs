"""
patch.py
This file contains the patches to be applied to the paho-mqtt library.
"""
import os
import shutil
import paho.mqtt.client as mqtt


client_path = mqtt.__file__
backup_path = client_path + ".bak"

# 创建备份文件
if not os.path.exists(backup_path):
    shutil.copyfile(client_path, backup_path)

with open(client_path, "r+", encoding="utf-8") as f:
    content = f.read()
    
    # WebSocket协议补丁
    original_websocket_code = """\
        elif callable(extra_headers):
            websocket_headers = extra_headers(websocket_headers)
"""

    patched_websocket_code = """\
        elif callable(extra_headers):
            # strict_patch_applied
            websocket_headers = extra_headers(websocket_headers)
            websocket_headers["Sec-Websocket-Protocol"] = extra_headers.get('Sec-WebSocket-Protocol', 'mqtt')
"""
    content.replace(original_websocket_code,patched_websocket_code)


    # PUBACK/PUBCOMP补丁
    original_pubackcomp_code = """\
    def _handle_pubackcomp(
        self, cmd: Literal['PUBACK'] | Literal['PUBCOMP']
    ) -> MQTTErrorCode:
        if self._protocol == MQTTv5:
            if self._in_packet['remaining_length'] < 2:
                return MQTTErrorCode.MQTT_ERR_PROTOCOL
        elif self._in_packet['remaining_length'] != 2:
            return MQTTErrorCode.MQTT_ERR_PROTOCOL
"""

    patched_puback_code = """\
    def _handle_pubackcomp(
        self, cmd: Literal['PUBACK'] | Literal['PUBCOMP']
    ) -> MQTTErrorCode:
        if self._protocol == MQTTv5:
            if self._in_packet['remaining_length'] < 2:
                return MQTTErrorCode.MQTT_ERR_PROTOCOL
        elif self._in_packet['remaining_length'] != 2:
            # strict_patch_applied
            self._in_packet["packet"] = self._in_packet["packet"][:2]
            self._in_packet['remaining_count'] = [2]
            self._in_packet["remaining_length"] = 2
"""
    content.replace(original_pubackcomp_code,patched_puback_code)

    # 回写文件
    f.seek(0)
    f.truncate()
    f.write(content)
