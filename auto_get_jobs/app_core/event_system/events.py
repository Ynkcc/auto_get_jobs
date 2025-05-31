# app_core/event_system/events.py
from typing import Any, Dict, Optional
import datetime
from app_core.models.job import JobStatus # 假设 JobStatus 在这里可以被导入

class BaseEvent:
    """
    所有事件的基类。
    包含一个时间戳，记录事件发生的时间。
    """
    def __init__(self, payload: Optional[Any] = None):
        self.timestamp: datetime.datetime = datetime.datetime.utcnow()
        self.payload: Optional[Any] = payload # 事件携带的数据

    def __str__(self):
        return f"{self.__class__.__name__}(timestamp={self.timestamp}, payload={self.payload})"

# --- 应用级事件 ---
class ApplicationStartedEvent(BaseEvent):
    """应用成功启动事件"""
    def __init__(self, config_path: str):
        super().__init__(payload={"config_path": config_path})

class ApplicationShutdownEvent(BaseEvent):
    """应用开始关闭事件"""
    pass # 通常不需要额外 payload

class ServiceStatusChangedEvent(BaseEvent):
    """某个服务状态发生变化 (启动/停止)"""
    def __init__(self, service_name: str, status: str, message: Optional[str] = None):
        # status 可以是 "STARTED", "STOPPED", "ERROR" 等
        super().__init__(payload={"service_name": service_name, "status": status, "message": message})

# --- 职位处理流程相关事件 ---
class JobCreatedEvent(BaseEvent):
    """当一个新的职位被首次从网站抓取并存入数据库时触发"""
    def __init__(self, job_pk_id: int, job_id_str: str, source_platform: str, title: str):
        super().__init__(payload={
            "job_pk_id": job_pk_id, # 数据库主键
            "job_id_str": job_id_str, # 网站原始ID
            "source_platform": source_platform,
            "title": title
        })

class JobStatusChangedEvent(BaseEvent):
    """当一个职位的状态发生改变时触发"""
    def __init__(self, job_pk_id: int, old_status: Optional[JobStatus], new_status: JobStatus, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "old_status": old_status.value if old_status else None, # 存储枚举的值
            "new_status": new_status.value, # 存储枚举的值
            "reason": reason, # 状态改变的原因，例如 "AI_ANALYSIS_COMPLETE", "USER_MANUAL_OVERRIDE"
            "details": details or {} # 其他相关细节，例如AI分析结果
        })

class JobAnalysisRequestedEvent(BaseEvent):
    """请求对特定职位进行AI分析 (例如，新职位创建后)"""
    def __init__(self, job_pk_id: int, job_description: str, resume_text: Optional[str] = None, job_title: Optional[str] = None):
        # resume_text 可以是默认简历或用户指定的简历
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "job_description": job_description,
            "resume_text": resume_text,
            "job_title": job_title
        })

class JobAnalysisCompletedEvent(BaseEvent):
    """AI分析完成事件"""
    def __init__(self, job_pk_id: int, match_score: int, analysis_details: Dict[str, Any]):
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "match_score": match_score,
            "analysis_details": analysis_details # 包含AI给出的原因、摘要等
        })

class JobDeliveryRequestedEvent(BaseEvent):
    """请求投递一个职位"""
    def __init__(self, job_pk_id: int, job_title: str, company_name: str):
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "job_title": job_title,
            "company_name": company_name
        })

class JobDeliveryStatusEvent(BaseEvent):
    """职位投递状态更新事件 (成功/失败)"""
    def __init__(self, job_pk_id: int, delivery_successful: bool, message: Optional[str] = None, error_details: Optional[str] = None):
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "delivery_successful": delivery_successful,
            "message": message,
            "error_details": error_details
        })

# --- GUI交互事件 (可选，如果GUI和后端通过事件通信) ---
class UserInterfaceLogEvent(BaseEvent):
    """请求在用户界面上记录一条消息"""
    def __init__(self, message: str, level: str = "info", source: Optional[str] = None):
        # level 可以是 "info", "warning", "error", "debug"
        # source 可以是产生日志的模块名
        super().__init__(payload={"message": message, "level": level, "source": source})

class UserManuallyMovedJobEvent(BaseEvent):
    """用户在GUI上手动拖动/更改了职位在看板上的位置 (暗示状态改变)"""
    def __init__(self, job_pk_id: int, target_column_status: JobStatus, source_column_status: Optional[JobStatus] = None):
        super().__init__(payload={
            "job_pk_id": job_pk_id,
            "target_column_status_value": target_column_status.value,
            "source_column_status_value": source_column_status.value if source_column_status else None,
        })

# 可以在这里根据需要定义更多具体的事件类型

if __name__ == '__main__':
    # 测试事件创建
    app_start = ApplicationStartedEvent("config/config.yaml")
    print(app_start)

    job_new = JobCreatedEvent(job_pk_id=1, job_id_str="xyz123", source_platform="Liepin", title="Python Developer")
    print(job_new)

    job_status_change = JobStatusChangedEvent(
        job_pk_id=1,
        old_status=JobStatus.NEW,
        new_status=JobStatus.ANALYZING,
        reason="自动进入分析流程"
    )
    print(job_status_change)

    ui_log = UserInterfaceLogEvent("测试UI日志消息", level="debug", source="TestModule")
    print(ui_log)
