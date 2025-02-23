# BOSS直聘自动化项目架构说明

##### 本段文字由 [deepseek-r1]() 生成

## 项目概述
基于Python实现的BOSS直聘自动化工具，主要功能包括：职位信息采集、智能匹配分析、自动投递简历、数据持久化存储。采用多进程+异步IO架构实现高效处理。

---

## 系统架构

### 1. 核心模块
```python
├── main.py                 # 主程序入口
├── job_processor.py        # 核心处理逻辑（多进程+异步IO）
├── utils_database.py       # 数据库管理模块
├── utils.py                # 基础工具库
├── utils_async.py          # 异步处理工具
└── user_requirements.md    # 用户简历
```
### 2. 模块职责说明

2.1 数据存储层 (utils_database.py)
```
class JobDetail(Base):           # 职位信息数据模型
class DatabaseManager:           # 数据库操作核心类
    ├── save_jobs_details()      # 数据存储主逻辑
    ├── filterVisited()          # 已访问职位过滤
    └── _upsert_records()        # 智能合并数据（新增/更新）
```
2.2 业务处理层 (job_processor.py)
```
class JobProcessor:              # 多进程任务处理器
    ├── _process_single_job()    # 单个职位处理流程
    ├── _process_batch()         # 批量任务调度
    └── start_processing()       # 启动异步处理循环
```
2.3 基础工具层

```
# utils.py
├── init_driver()               # 浏览器驱动初始化
├── filterJobsBySalary()        # 薪资过滤器
└── parseParams()               # URL参数解析器

# utils_async.py
├── aiHrCheck()                # AI匹配度分析
├── getJobInfo()               # 异步获取职位详情
└── startChat()                # 发起沟通接口
```
---

```
graph TD
    A[主程序启动] --> B[浏览器初始化]
    B --> C[自动登录/加载cookies]
    C --> D[构造搜索URL]
    D --> E[获取职位列表]
    E --> F[薪资过滤+去重过滤]
    F --> G[子进程任务分发]
    G --> H{AI智能匹配}
    H -->|匹配成功| I[自动投递简历]
    H -->|匹配失败| J[标记为已访问]
    I --> K[结果持久化存储]
```