# src/utils/event_manager.py
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class EventManager:
    """
    一个单例的异步事件管理器，作为事件总线。
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = defaultdict(list)
        return cls._instance

    def subscribe(self, event_type: str, handler):
        """
        订阅一个事件。
        处理函数必须是协程 (async def)。
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"事件处理程序 {handler.__name__} 必须是协程 (async def)")
        self._listeners[event_type].append(handler)
        logger.debug(f"处理器 {handler.__name__} 已订阅事件 '{event_type}'")

    async def publish(self, event_type: str, *args, **kwargs):
        """
        发布一个事件，并异步并发地执行所有订阅者的处理函数。
        """
        if event_type not in self._listeners:
            logger.debug(f"事件 '{event_type}' 被发布，但没有订阅者")
            return

        logger.info(f"发布事件 '{event_type}'，有 {len(self._listeners[event_type])} 个订阅者")
        tasks = [handler(*args, **kwargs) for handler in self._listeners[event_type]]
        
        # 使用 return_exceptions=True 来防止一个处理器的异常中断其他处理器
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"事件 '{event_type}' 的一个处理器在执行时发生异常: {result}", exc_info=result)

# 创建一个全局实例，方便在项目中各处调用
event_manager = EventManager()