# 开发者文档

## 数据流图

```mermaid
graph LR
    A[main.py] --> B(config/config.yaml);
    B --> C{日志配置};
    A --> D[JobHandler];
    A --> E[WsClient];
    A --> F[DatabaseManager];
    A --> G{用户登录};
    G --> H{构建搜索URL};
    H --> I{循环搜索};
    I --> J[职位信息];
    J --> K(job_queue);
    K --> L[JobHandler];
    L --> M{薪资过滤};
    M --> N{数据库过滤};
    N --> O{AI分析};
    O -- 匹配 --> P{发送打招呼语};
    P --> Q(WsClient);
    O -- 不匹配 --> R{保存职位信息};
    L --> R;
    Q --> S(WebSocket服务器);
    A --> T{程序退出};
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#ccf,stroke:#333,stroke-width:2px
    style E fill:#ccf,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
```

## 流程说明

1.  **程序启动**: `main.py` 作为程序入口，加载 `config/config.yaml` 配置文件。
2.  **日志配置**: 根据配置文件配置日志系统。
3.  **初始化**: 初始化 `JobHandler`, `WsClient`, `DatabaseManager` 等组件。
4.  **用户登录**: 使用 Playwright 模拟用户登录 BOSS 直聘网站。
5.  **构建搜索 URL**: 根据配置文件中的 `job_search` 参数，构建搜索 URL 列表。
6.  **循环搜索**: 循环遍历搜索 URL 列表，访问每个 URL，获取职位信息。
7.  **职位信息处理**:
    *   将获取到的职位信息放入 `job_queue` 队列。
    *   `JobHandler` 从 `job_queue` 队列中取出职位信息。
    *   根据配置的 `salary_range` 过滤职位。
    *   从数据库中过滤掉已经访问过的职位。
    *   使用 AI 分析职位是否匹配。
    *   如果匹配，则发送打招呼语（如果启用 AI 打招呼语）。
    *   将职位信息保存到数据库。
8.  **WebSocket 通信**: `WsClient` 负责与 WebSocket 服务器通信，发送打招呼语等消息。
9.  **程序退出**: 接收到停止信号后，程序退出。
