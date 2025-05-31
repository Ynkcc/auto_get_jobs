# app_core/event_system/event_bus.py
import logging
from collections import defaultdict
from typing import Callable, Type, Dict, List, Any
import threading # 用于线程安全

from .events import BaseEvent # 导入事件基类

logger = logging.getLogger(__name__)

class EventBus:
    """
    一个简单的同步事件总线。
    允许订阅者注册对特定事件类型的回调函数。
    当事件被发布时，所有相关的订阅者回调都会被同步调用。
    """
    def __init__(self):
        # 使用 defaultdict(list) 来存储事件类型到其处理器列表的映射
        # self._subscribers: Dict[Type[BaseEvent], List[Callable[[BaseEvent], None]]] = defaultdict(list)
        # 为了支持异步处理器，或者需要更多上下文的处理器，可以考虑存储更复杂的对象
        self._subscribers: Dict[Type[BaseEvent], List[Callable]] = defaultdict(list)
        self._lock = threading.RLock() # 可重入锁，用于确保订阅和发布的线程安全
        logger.info("事件总线 EventBus 已初始化。")

    def subscribe(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]):
        """
        订阅一个事件类型。
        当指定类型的事件被发布时，提供的处理器 (handler) 将被调用。

        :param event_type: 要订阅的事件类 (例如 JobCreatedEvent)。
        :param handler: 一个可调用对象，它接受一个 BaseEvent (或其子类) 的实例作为参数。
        """
        if not callable(handler):
            raise TypeError(f"事件处理器 {handler} 必须是可调用的。")
        if not issubclass(event_type, BaseEvent):
            raise TypeError(f"事件类型 {event_type} 必须是 BaseEvent 的子类。")

        with self._lock:
            # logger.debug(f"订阅事件类型 {event_type.__name__}，处理器: {getattr(handler, '__name__', str(handler))}")
            self._subscribers[event_type].append(handler)
            # logger.debug(f"当前 {event_type.__name__} 的订阅者数量: {len(self._subscribers[event_type])}")


    def unsubscribe(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]):
        """
        取消订阅一个事件处理器。

        :param event_type: 事件类。
        :param handler: 要移除的处理器。
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    # logger.debug(f"已取消订阅事件类型 {event_type.__name__} 的处理器: {getattr(handler, '__name__', str(handler))}")
                    if not self._subscribers[event_type]: # 如果列表为空，可以从字典中移除键
                        del self._subscribers[event_type]
                except ValueError:
                    logger.warning(f"尝试取消订阅一个未注册的处理器 {getattr(handler, '__name__', str(handler))} for event {event_type.__name__}")
            else:
                logger.warning(f"尝试取消订阅一个没有订阅者的事件类型: {event_type.__name__}")


    def publish(self, event: BaseEvent):
        """
        发布一个事件。
        所有订阅了此事件类型（或其父事件类型，如果支持继承发布）的处理器都将被调用。
        目前是同步调用。

        :param event: 要发布的事件实例。
        """
        if not isinstance(event, BaseEvent):
            logger.error(f"尝试发布一个非 BaseEvent 类型的对象: {type(event)}")
            return

        event_type_to_publish = type(event)
        # logger.debug(f"正在发布事件: {event}")

        handlers_to_call: List[Callable[[BaseEvent], None]] = []
        with self._lock: # 获取订阅者列表时加锁
            # 获取直接订阅该事件类型的处理器
            if event_type_to_publish in self._subscribers:
                handlers_to_call.extend(self._subscribers[event_type_to_publish])
            
            # (可选) 支持事件继承：如果发布了子类事件，父类事件的订阅者也应该收到通知。
            # 例如，如果有人订阅了 BaseEvent，任何事件发布时他们都应该收到。
            # 这可以通过遍历事件的MRO (Method Resolution Order) 来实现。
            # for ancestor_type in event_type_to_publish.mro():
            #     if ancestor_type in self._subscribers and ancestor_type != event_type_to_publish:
            #         # 避免重复添加已经为精确类型添加的处理器
            #         for handler in self._subscribers[ancestor_type]:
            #             if handler not in handlers_to_call: # 简单检查，可能不够高效
            #                 handlers_to_call.append(handler)

        if not handlers_to_call:
            # logger.debug(f"事件 {event_type_to_publish.__name__} 没有订阅者。")
            return

        # logger.debug(f"为事件 {event_type_to_publish.__name__} 找到 {len(handlers_to_call)} 个处理器。开始调用...")
        for handler in handlers_to_call:
            try:
                # logger.debug(f"  -> 调用处理器 {getattr(handler, '__name__', str(handler))} 处理事件 {event}")
                handler(event) # 同步调用
            except Exception as e:
                logger.error(f"事件处理器 {getattr(handler, '__name__', str(handler))} 在处理事件 {event} 时发生错误: {e}", exc_info=True)
                # 根据需要，可以决定是否因为一个处理器的错误而停止其他处理器的执行

    def clear_all_subscribers(self):
        """移除所有事件类型的所有订阅者 (主要用于测试或应用关闭时)。"""
        with self._lock:
            self._subscribers.clear()
            logger.info("事件总线：所有订阅者已被清除。")

# 全局事件总线实例 (单例模式的简单实现)
# 在实际应用中，这个实例会被 AppController 创建和管理，并通过依赖注入传递给需要的模块。
# global_event_bus = EventBus()

if __name__ == '__main__':
    # --- 事件总线测试 ---
    from .events import JobCreatedEvent, JobStatusChangedEvent, ApplicationStartedEvent, BaseEvent # 从当前目录导入
    from app_core.models.job import JobStatus # 假设JobStatus可导入

    bus = EventBus()

    # 定义一些事件处理器
    def handle_job_created(event: JobCreatedEvent):
        print(f"[CREATED_HANDLER] 新职位创建: ID={event.payload['job_pk_id']}, 标题='{event.payload['title']}'")

    def handle_job_status_change(event: JobStatusChangedEvent):
        print(f"[STATUS_HANDLER] 职位状态变更: ID={event.payload['job_pk_id']}, 从 {event.payload['old_status']} 到 {event.payload['new_status']}")

    def handle_app_start(event: ApplicationStartedEvent):
        print(f"[APP_START_HANDLER] 应用启动，配置文件: {event.payload['config_path']}")

    def handle_any_event(event: BaseEvent): # 订阅基类事件
        print(f"[ANY_EVENT_HANDLER] 捕获到事件: {event.__class__.__name__} - {event.payload}")


    # 订阅事件
    bus.subscribe(JobCreatedEvent, handle_job_created)
    bus.subscribe(JobStatusChangedEvent, handle_job_status_change)
    bus.subscribe(ApplicationStartedEvent, handle_app_start)
    # bus.subscribe(BaseEvent, handle_any_event) # 测试订阅基类

    # 发布事件
    print("\n--- 发布事件 ---")
    bus.publish(ApplicationStartedEvent(config_path="config/test_config.yaml"))
    bus.publish(JobCreatedEvent(job_pk_id=101, job_id_str="abc", source_platform="Test", title="软件工程师"))
    bus.publish(JobStatusChangedEvent(job_pk_id=101, old_status=JobStatus.NEW, new_status=JobStatus.ANALYZING))
    bus.publish(JobCreatedEvent(job_pk_id=102, job_id_str="def", source_platform="Test", title="产品经理"))
    
    # 测试发布一个没有订阅者的事件
    class UnsubscribedEvent(BaseEvent): pass
    bus.publish(UnsubscribedEvent(payload="无订阅者数据"))


    # 测试取消订阅
    print("\n--- 取消订阅 handle_job_created ---")
    bus.unsubscribe(JobCreatedEvent, handle_job_created)
    bus.publish(JobCreatedEvent(job_pk_id=103, job_id_str="ghi", source_platform="Test", title="UI设计师 (此条不应被handle_job_created处理)"))
    # handle_any_event 仍会处理（如果订阅了BaseEvent）

    print("\n--- 清除所有订阅者 ---")
    bus.clear_all_subscribers()
    bus.publish(ApplicationStartedEvent(config_path="config/another.yaml")) # 不会有处理器响应

    print("\n--- 测试完成 ---")
