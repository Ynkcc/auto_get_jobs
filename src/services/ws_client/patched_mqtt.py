# src/ws_client/patch_client.py
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class patch_client(mqtt.Client):
    """
    PUBACK/PUBCOMP补丁
    """
    def __init__(self, *args, **kwargs):
        # 调用父类的构造函数
        super().__init__(*args, **kwargs)
    def _handle_pubackcomp(self, *args, **kwargs):
        """
        处理PUBACK/PUBCOMP消息
        """
        if self._protocol == mqtt.MQTTv5:
            if self._in_packet['remaining_length'] < 2:
                return mqtt.MQTTErrorCode.MQTT_ERR_PROTOCOL
        elif self._in_packet['remaining_length'] != 2:
            # strict_patch_applied
            self._in_packet["packet"] = self._in_packet["packet"][:2]
            self._in_packet['remaining_count'] = [2]
            self._in_packet["remaining_length"] = 2
        return super()._handle_pubackcomp()
    