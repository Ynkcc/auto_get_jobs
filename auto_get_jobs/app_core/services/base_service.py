# app_core/services/base_service.py
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional

# 避免循环导入 AppController，如果需要 AppController 的引用，使用类型提示并后期注入
# from app_core.app_controller import AppController # <--- 暂时注释，改为类型提示

logger = logging.getLogger(__name__)

class BaseService(ABC):
    def __init__(self, config: dict, db_manager, ui_updater, stop_event: threading.Event, app_controller = None): # app_controller: 'AppController'
        """
        服务模块的基类。
        :param config: 该服务相关的配置字典。
        :param db_manager: DatabaseManager 实例。
        :param ui_updater: UI更新器接口实例。
        :param stop_event: 用于通知服务停止的 threading.Event。
        :param app_controller: (可选) AppController 的引用，用于服务间通信或调用通用功能。
        """
        self.config = config
        self.db_manager = db_manager
        self.ui_updater = ui_updater
        self.stop_event = stop_event
        self.app_controller = app_controller # AppController 的引用
        
        self._thread: Optional[threading.Thread] = None # 服务运行的线程
        self._is_running = False # 服务当前是否正在运行的标志

        self.service_name = self.__class__.__name__
        logger.info(f"{self.service_name} 初始化。")

    def _log_to_ui(self, message: str, level: str = "info"):
        """通过UI更新器发送日志消息 (如果可用)"""
        if self.ui_updater and hasattr(self.ui_updater, 'log'):
            if hasattr(self.ui_updater, 'schedule_gui_task'): # 确保在GUI线程执行
                self.ui_updater.schedule_gui_task(self.ui_updater.log, f"[{self.service_name}] {message}", level)
            else:
                self.ui_updater.log(f"[{self.service_name}] {message}", level) # 尽力而为
        else:
            logger.info(f"[{self.service_name}] {message}") # 回退到标准日志

    @abstractmethod
    def _run(self):
        """
        服务的主要运行逻辑。子类必须实现此方法。
        此方法将在单独的线程中执行。
        它应该定期检查 self.stop_event.is_set() 并在需要时优雅退出。
        """
        pass

    def start(self):
        """启动服务。"""
        if self._is_running:
            logger.warning(f"{self.service_name} 已在运行中。")
            return

        self.stop_event.clear() # 清除停止信号
        self._is_running = True
        
        # 创建并启动新线程
        self._thread = threading.Thread(target=self._service_wrapper, daemon=True, name=self.service_name)
        self._thread.start()
        logger.info(f"{self.service_name} 已启动。")
        self._log_to_ui("服务已启动。", "info")

    def _service_wrapper(self):
        """包装 _run 方法以处理启动和停止日志以及错误处理。"""
        logger.info(f"{self.service_name} 运行线程开始。")
        try:
            self._run() # 调用子类的实现
        except Exception as e:
            logger.error(f"{self.service_name} 在运行过程中发生严重错误: {e}", exc_info=True)
            self._log_to_ui(f"服务发生严重错误: {e}", "error")
        finally:
            self._is_running = False # 确保在线程退出时更新状态
            logger.info(f"{self.service_name} 运行线程已结束。")
            self._log_to_ui("服务已停止。", "info")


    def stop(self, wait_for_completion: bool = False, timeout: Optional[float] = 5.0):
        """
        请求服务停止。
        :param wait_for_completion: 是否等待服务线程执行完毕。
        :param timeout: 等待超时时间（秒），仅当 wait_for_completion 为 True 时有效。
        """
        if not self._is_running and not (self._thread and self._thread.is_alive()): # 如果本就没运行
            logger.info(f"{self.service_name} 未运行或已停止。")
            return

        logger.info(f"正在请求停止 {self.service_name}...")
        self.stop_event.set() # 设置停止信号

        if wait_for_completion and self._thread and self._thread.is_alive():
            logger.info(f"等待 {self.service_name} 线程 (ID: {self._thread.ident}) 完成...")
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(f"{self.service_name} 线程未能在 {timeout} 秒内结束。")
            else:
                logger.info(f"{self.service_name} 线程已成功结束。")
        
        # _is_running 应该在 _service_wrapper 的 finally 中被设置为 False
        # 但作为双重保险，如果线程已经结束，可以再次设置
        if self._thread is None or not self._thread.is_alive():
            self._is_running = False

        logger.info(f"{self.service_name} 已被请求停止。")


    def is_running(self) -> bool:
        """检查服务当前是否正在运行。"""
        # 考虑线程可能已结束但 _is_running 标志尚未更新的情况（尽管 _service_wrapper 应该处理）
        if self._thread and not self._thread.is_alive() and self._is_running:
            self._is_running = False # 同步状态
        return self._is_running

    # --- 可选的通用辅助方法 ---
    def _submit_app_controller_task(self, coro, callback=None):
        """如果服务需要向AppController的事件循环提交任务"""
        if self.app_controller and hasattr(self.app_controller, 'submit_async_task'):
            return self.app_controller.submit_async_task(coro, callback)
        else:
            logger.warning(f"{self.service_name} 无法提交任务：AppController 不可用或缺少 submit_async_task 方法。")
            if callback:
                try: callback(RuntimeError("AppController不可用"))
                except: pass
            return None

