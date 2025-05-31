### proto 描述文件获取方式

*   **浏览器控制台提取:**  进入Boss直聘官网后在浏览器控制台输入 `window.__PROTO_FILE_VAR__`，提取输出结果。
*   **添加 `syntax`:**  在提取的输出结果头部添加 `syntax = "proto2";`。
*   **命名文件:**  将完整内容保存为 `techwolf.proto` 文件。

# WsClient 说明文档

## 1. 简介

`src/ws_client/` 目录包含用于实现 WebSocket 客户端的 Python 代码，该客户端用于与 Boss直聘网站进行聊天功能交互。


### 2.1. 连接建立与维护

*   **WebSocket 连接:**  `WsClient` 使用 `paho-mqtt` 库建立 WebSocket 连接，并使用 MQTT 协议进行通信。
*   **自动重连:**  客户端具有自动重连机制，在连接断开后会自动尝试重新连接。
*   **配置更新:**  客户端能够从 `utils.session_manager` 获取最新的 cookies 和 headers 信息，并动态更新连接配置。

### 2.2. 消息发送与接收

*   **消息发送:**  支持发送文本消息和图片消息。消息内容通过 Protobuf 序列化后发送。
*   **消息接收:**  接收并解析来自服务器的消息，根据消息类型进行处理。
*   **消息类型处理:**  能够处理聊天消息、简历请求等多种消息类型。

### 2.3. 协议解析 (Protobuf)

*   **Protobuf 定义:**  使用 `techwolf.proto` 文件定义消息协议。
*   **Python 实现:**  通过 `protobuf` 编译器将 `techwolf.proto` 文件生成 `techwolf_pb2.py` 文件，用于 Python 代码中的消息序列化和反序列化。

## 3. 代码结构

### 3.1. 主要类: `WsClient`

*   **`WsClient` 类:**  是 WebSocket 客户端的核心实现类，继承自 `threading.Thread`，实现客户端的初始化、连接、消息发送接收、重连等功能。
*   **回调函数:**  `WsClient` 类中定义了多个回调函数，用于处理连接事件、消息接收事件等。例如 `_on_connect`, `_on_message`, `_on_disconnect` 等。

### 3.2. 关键模块与交互

*   **`utils.general`:**  提供通用工具函数，例如 `get_user_info`, `get_wt2`, `upload_image` 等，用于获取用户信息、动态密码、上传图片等功能。
*   **`utils.session_manager`:**  用于管理用户会话，提供最新的 cookies 和 headers 信息。
*   **`utils.config_manager`:**  用于管理配置信息，例如简历图片文件路径、是否发送简历图片等。
*   **`paho-mqtt`:**  MQTT 客户端库，用于建立 WebSocket 连接和 MQTT 协议通信。
*   **`techwolf_pb2.py`:**  Protobuf 生成的 Python 文件，用于消息序列化和反序列化。

## 4. paho-mqtt 源码修改

为了解决与 Boss直聘 MQTT 服务器的兼容性问题，需要对 `paho-mqtt` 库的源码进行修改。
> ##### ps：只有`4.2`是必要的

### 4.1. `Sec-WebSocket-Protocol` 修改

*   **问题:**  `paho-mqtt` 源码可能会覆盖 `Sec-WebSocket-Protocol` header，导致与网页端不一致。
*   **修改方案:**  修改 `paho-mqtt` 源码，确保 `Sec-WebSocket-Protocol` header 可以自定义设置。
*   **修改位置:**  `paho-mqtt/client.py` 文件中 `_WebsocketWrapper` 类的 `_do_handshake` 函数。
*   **代码示例:**

```python
        elif callable(extra_headers):
            websocket_headers = extra_headers(websocket_headers)
            + websocket_headers["Sec-Websocket-Protocol"] = extra_headers.get('Sec-WebSocket-Protocol', 'mqtt')
        header = "\\r\\n".join([
            f"GET {self._path} HTTP/1.1",
            "\\r\\n".join(f"{i}: {j}" for i, j in websocket_headers.items()),
            "\\r\\n",
        ]).encode("utf8")
```

### 4.2. `PUBACK` 格式修改

*   **问题:**  Boss直聘 WebSocket 服务器返回的 `PUBACK` 消息格式不符合 MQTT v3.1.1 标准，导致 `paho-mqtt` 客户端解析错误，返回 `MQTTErrorCode.MQTT_ERR_PROTOCOL` 错误码 (code 2)。
*   **修改方案:**  修改 `paho-mqtt` 源码，兼容 Boss直聘的 `PUBACK` 消息格式。
*   **修改位置:**  `paho-mqtt/client.py` 文件中 `Client` 类的 `_handle_pubackcomp` 函数。
*   **代码示例:**

```python
        if self._protocol == MQTTv5:
            if self._in_packet['remaining_length'] < 2:
                return MQTTErrorCode.MQTT_ERR_PROTOCOL
        elif self._in_packet['remaining_length'] != 2:
                - return MQTTErrorCode.MQTT_ERR_PROTOCOL
            + self._in_packet["packet"] = self._in_packet["packet"][:2]
            + self._in_packet['remaining_count'] = [2]
            + self._in_packet["remaining_length"] = 2
```

### 4.3. 连接丢失问题 (`MQTT_ERR_CONN_LOST`)

*   **问题:**  客户端偶现连接丢失问题，错误码为 `MQTT_ERR_CONN_LOST` (code 7)，怀疑与 Python GIL 导致连接超时有关。
*   **尝试解决方案:**  修改 `paho-mqtt` 源码，将连接断开错误 (`MQTT_ERR_CONN_LOST`) 转换为非致命错误 (`MQTT_ERR_AGAIN`)，避免程序退出。
*   **修改位置:**  `paho-mqtt/client.py` 文件中 `Client` 类的 `_packet_read` 函数。
*   **代码示例:**

```python
        if self._in_packet['command'] == 0:
            try:
                command = self._sock_recv(1)
            except BlockingIOError:
                return MQTTErrorCode.MQTT_ERR_AGAIN
            except TimeoutError as err:
                self._easy_log(
                    MQTT_LOG_ERR, 'timeout on socket: %s', err)
                return MQTTErrorCode.MQTT_ERR_CONN_LOST
            except OSError as err:
                self._easy_log(
                    MQTT_LOG_ERR, 'failed to receive on socket: %s', err)
                return MQTTErrorCode.MQTT_ERR_CONN_LOST
            else:
                if len(command) == 0:
                    - return MQTTErrorCode.MQTT_ERR_CONN_LOST
                    + return MQTTErrorCode.MQTT_ERR_AGAIN
                self._in_packet['command'] = command[0]
```

## 5. 参考资料

*   [bossbot](https://github.com/xmiaoq/bossbot)
*   [ai-job](https://github.com/yangfeng20/ai-job)
*   [MQTT v3.1.1 标准文档](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
*   [protocolbuffers/protobuf](https://github.com/protocolbuffers/protobuf)
