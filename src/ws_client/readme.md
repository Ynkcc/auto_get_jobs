相关实现参考以下项目

`https://github.com/xmiaoq/bossbot`
`https://github.com/yangfeng20/ai-job`

### 提取proto描述文件
浏览器控制台输入 `window.__PROTO_FILE_VAR__`,
提取输出结果后加上
```
syntax = "proto2";
```
命名为 `techwolf.proto`
下载 `https://github.com/protocolbuffers/protobuf`
执行 `.\protoc --python_out=. techwolf.proto`
生成`techwolf_pb2.py`
username(token) getUserInfo()得到，原字符串后+'|0' 静态
password /wapi/zppassport/get/wt 得到 get请求 动态变化

CLIENT_ID ，`ws-`+16位英文字母

```
			"Sec-WebSocket-Protocol": "mqtt",
		}

        # This is checked in ws_set_options so it will either be None, a
        # dictionary, or a callable
        if isinstance(extra_headers, dict):
=======
			"Sec-WebSocket-Protocol": websocket_headers.get('Sec-WebSocket-Protocol', 'mqtt'),
		}

        # This is checked in ws_set_options so it will either be None, a
        # dictionary, or a callable
        if isinstance(extra_headers, dict):

```