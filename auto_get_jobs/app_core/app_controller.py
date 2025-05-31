# app_core/app_controller.py
import asyncio
import logging
import threading
from typing import Optional, List, Callable, Any

from .utils.config_manager import ConfigManager # 假设ConfigManager是可导入的类型
from .db.database_manager import DatabaseManager
from .models.job import Job, JobStatus

# 导入服务类 (骨架，后续会创建)
from .services.base_service import BaseService
from .services.crawler_service import CrawlerService
# from .services.ai_analysis_service import AiAnalysisService # 假设后续会创建
# from .services.delivery_service import DeliveryService     # 假设后续会创建

logger = logging.getLogger(__name__)

class AppController:
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager, ui_updater: Optional[object]):
        """
        应用总控制器。
        :param config: 应用配置对象。
        :param db_manager: 数据库管理器实例。
        :param ui_updater: GUI更新器接口实例，用于将更新推送到GUI。
                           应有方法如 .log(msg, level), .update_job_display(job_id), .schedule_gui_task(callable, *args)
        """
        self.config = config
        self.db_manager = db_manager
        self.ui_updater = ui_updater

        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_loop_thread: Optional[threading.Thread] = None
        self._async_loop_ready_event = asyncio.Event() # 用于同步事件循环的启动

        self.services: List[BaseService] = []
        self._initialize_services()

        self._stop_event = threading.Event() # 全局停止信号给所有内部线程/任务

        logger.info("AppController 初始化完成。")

    def _log_to_ui(self, message: str, level: str = "info"):
        """通过UI更新器发送日志消息 (如果可用)"""
        if self.ui_updater and hasattr(self.ui_updater, 'log'):
            # 确保在GUI线程中调用
            if hasattr(self.ui_updater, 'schedule_gui_task'):
                self.ui_updater.schedule_gui_task(self.ui_updater.log, message, level)
            else: # 尽力而为，但可能不是线程安全的
                self.ui_updater.log(message, level)
        else: # 回退到标准日志
            if level == "error": logger.error(message)
            elif level == "warning": logger.warning(message)
            else: logger.info(message)

    def _run_async_event_loop(self):
        """在单独的线程中运行asyncio事件循环。"""
        logger.info("启动AppController的内部asyncio事件循环...")
        try:
            self._async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._async_loop)
            self._async_loop_ready_event.set() # 通知事件循环已准备好
            self._async_loop.run_forever()
        except Exception as e:
            logger.error(f"AppController的asyncio事件循环异常终止: {e}", exc_info=True)
        finally:
            if self._async_loop and self._async_loop.is_running():
                self._async_loop.call_soon_threadsafe(self._async_loop.stop)
            logger.info("AppController的内部asyncio事件循环已停止。")

    def _ensure_async_loop_running(self):
        """确保asyncio事件循环正在运行，如果不是则启动它。"""
        if self._async_loop_thread is None or not self._async_loop_thread.is_alive():
            self._async_loop_ready_event.clear()
            self._async_loop_thread = threading.Thread(target=self._run_async_event_loop, daemon=True, name="AppCtrlAsyncLoop")
            self._async_loop_thread.start()
            logger.info("等待asyncio事件循环初始化...")
            # 等待事件循环真正启动并设置self._async_loop
            # 在实际使用 run_coroutine_threadsafe 前确保循环已就绪
            # 可以使用 self._async_loop_ready_event.wait(timeout=5)
            if not self._async_loop_ready_event.wait(timeout=10): # 等待10秒
                 logger.error("Asyncio事件循环未能及时就绪！")
                 raise RuntimeError("Asyncio事件循环未能及时就绪！")
            logger.info("Asyncio事件循环已就绪。")

    def submit_async_task(self, coro: asyncio.coroutine, callback: Optional[Callable[[Any], None]] = None) -> Optional[asyncio.Future]:
        """
        安全地将协程提交到内部事件循环执行。
        :param coro: 要执行的协程。
        :param callback: (可选) 协程完成后在事件循环线程中调用的回调函数，接收协程结果或异常。
        :return: 一个asyncio.Future对象，如果事件循环未运行则返回None。
        """
        if not self._async_loop or not self._async_loop.is_running():
            self._log_to_ui("错误: 异步事件循环未运行，无法提交任务。", "error")
            logger.error("异步事件循环未运行，无法提交任务。")
            if callback:
                try: callback(RuntimeError("事件循环未运行"))
                except: pass
            return None

        future = asyncio.run_coroutine_threadsafe(coro, self._async_loop)
        
        if callback:
            def _done_callback(f):
                try:
                    result = f.result()
                    callback(result)
                except Exception as e:
                    logger.error(f"AppController提交的异步任务执行出错: {e}", exc_info=True)
                    callback(e) # 将异常传递给回调
            future.add_done_callback(_done_callback)
            
        return future

    def _initialize_services(self):
        """初始化所有服务模块。"""
        logger.info("开始初始化服务模块...")
        # CrawlerService
        try:
            crawler_config = self.config.get('crawler', {}) # 从总配置中获取爬虫配置
            # CrawlerService 需要 playwright_config, search_url_config, db_manager, stop_event 等
            # 它也需要一种方式将抓取到的原始职位数据放入一个队列或直接写入数据库
            self.services.append(CrawlerService(crawler_config, self.db_manager, self.ui_updater, self._stop_event, self))
            logger.info("CrawlerService 已加入服务列表。")
        except Exception as e:
            logger.error(f"初始化 CrawlerService 失败: {e}", exc_info=True)

        # AiAnalysisService (假设后续创建)
        # try:
        #     ai_config = self.config.get('ai', {})
        #     self.services.append(AiAnalysisService(ai_config, self.db_manager, self.ui_updater, self._stop_event, self))
        #     logger.info("AiAnalysisService 已加入服务列表。")
        # except Exception as e:
        #     logger.error(f"初始化 AiAnalysisService 失败: {e}", exc_info=True)

        # DeliveryService (假设后续创建)
        # try:
        #     ws_client_config = self.config.get('ws_client', {})
        #     self.services.append(DeliveryService(ws_client_config, self.db_manager, self.ui_updater, self._stop_event, self))
        #     logger.info("DeliveryService 已加入服务列表。")
        # except Exception as e:
        #     logger.error(f"初始化 DeliveryService 失败: {e}", exc_info=True)
        
        logger.info(f"共初始化 {len(self.services)} 个服务模块。")


    def start_all_services(self):
        """启动所有已初始化的服务。"""
        self._ensure_async_loop_running() # 确保事件循环已启动，供服务内部可能使用 submit_async_task
        self._stop_event.clear()
        logger.info("正在启动所有服务...")
        for service in self.services:
            try:
                service.start() # BaseService应有start方法
                logger.info(f"服务 {service.__class__.__name__} 已启动。")
            except Exception as e:
                self._log_to_ui(f"启动服务 {service.__class__.__name__} 失败: {e}", "error")
                logger.error(f"启动服务 {service.__class__.__name__} 失败: {e}", exc_info=True)
        self._log_to_ui("所有服务已尝试启动。", "info")

    def stop_all_services(self):
        """停止所有正在运行的服务。"""
        logger.info("正在请求停止所有服务...")
        self._stop_event.set() # 设置全局停止信号
        for service in self.services:
            try:
                service.stop() # BaseService应有stop方法
                logger.info(f"服务 {service.__class__.__name__} 已请求停止。")
            except Exception as e:
                self._log_to_ui(f"停止服务 {service.__class__.__name__} 时发生错误: {e}", "error")
                logger.error(f"停止服务 {service.__class__.__name__} 时发生错误: {e}", exc_info=True)
        self._log_to_ui("所有服务已请求停止。", "info")

    def is_any_service_running(self) -> bool:
        """检查是否有任何服务仍在运行。"""
        for service in self.services:
            if service.is_running(): # BaseService应有is_running方法
                return True
        return False

    def shutdown(self):
        """彻底关闭AppController和所有资源。"""
        logger.info("AppController 开始执行关闭流程...")
        self.stop_all_services() # 确保所有服务被要求停止

        # 等待服务线程结束 (可选，但推荐)
        # for service in self.services:
        #     if hasattr(service, '_thread') and service._thread and service._thread.is_alive():
        #         logger.info(f"等待服务 {service.__class__.__name__} 线程结束...")
        #         service._thread.join(timeout=5) # 给5秒超时
        #         if service._thread.is_alive():
        #             logger.warning(f"服务 {service.__class__.__name__} 线程未能及时结束。")

        if self._async_loop and self._async_loop.is_running():
            logger.info("正在关闭内部asyncio事件循环...")
            # 确保所有挂起的任务有机会完成或被取消
            # self._async_loop.call_soon_threadsafe(self._async_loop.stop) # 已在 _run_async_event_loop 的 finally 中
            if self._async_loop_thread and self._async_loop_thread.is_alive():
                self._async_loop_thread.join(timeout=5) # 等待事件循环线程结束
                if self._async_loop_thread.is_alive():
                     logger.warning("Asyncio事件循环线程未能及时结束。")
        
        logger.info("AppController 关闭完成。")

    # --- GUI交互方法 (示例) ---
    async def get_jobs_for_display_async(self, statuses: List[JobStatus], limit: int = 50, offset: int = 0) -> List[Job]:
        """(异步) 获取用于GUI显示的职位列表"""
        # 注意：数据库操作本身可能是同步的，除非使用异步ORM和驱动
        # 这里的方法是异步的，因为它可能被GUI通过 submit_async_task 调用
        self._log_to_ui(f"正在获取状态为 {statuses} 的职位...", "debug")
        try:
            # db_manager 的方法是同步的，直接调用即可
            jobs = self.db_manager.get_jobs_by_status(statuses, limit, offset)
            self._log_to_ui(f"成功获取 {len(jobs)} 条职位用于显示。", "debug")
            return jobs
        except Exception as e:
            self._log_to_ui(f"获取职位列表时发生错误: {e}", "error")
            logger.error(f"获取职位列表时发生错误: {e}", exc_info=True)
            return []

    async def manually_change_job_pipeline_status_async(self, job_pk_id: int, new_status: JobStatus, old_status: Optional[JobStatus] = None, user_notes: Optional[str] = None) -> dict:
        """
        (异步) 处理用户从GUI手动更改职位流程状态的请求。
        :param job_pk_id: 职位的主键ID。
        :param new_status: 用户指定的新状态。
        :param old_status: (可选) 职位在GUI上的旧状态，用于校验或记录。
        :param user_notes: (可选) 用户提供的操作备注。
        :return: 一个包含操作结果的字典，例如 {"success": True, "job_id": job_pk_id} 或 {"success": False, "error": "消息"}
        """
        self._log_to_ui(f"用户请求更改职位 PK_ID:{job_pk_id} 的状态为 {new_status} (原状态: {old_status or '未知'})", "info")
        
        update_details = {"is_manual_override": True}
        if user_notes:
            update_details["user_notes"] = user_notes

        updated_job = self.db_manager.update_job_status(job_pk_id, new_status, details=update_details)

        if updated_job:
            self._log_to_ui(f"职位 PK_ID:{job_pk_id} 状态已成功更新为 {new_status}。", "info")
            # TODO: 根据新状态触发相应服务的逻辑
            # 例如，如果 new_status 是 MATCHED 或 QUEUED_FOR_DELIVERY,
            # 可能需要通知 DeliveryService (如果它不主动轮询的话)
            # if new_status == JobStatus.QUEUED_FOR_DELIVERY:
            #    delivery_svc = next((s for s in self.services if isinstance(s, DeliveryService)), None)
            #    if delivery_svc:
            #        delivery_svc.add_job_to_queue(updated_job.id) # 假设有这样的方法

            # 通知GUI更新此职位（以及可能的列表）
            if self.ui_updater and hasattr(self.ui_updater, 'update_job_in_display'):
                 if hasattr(self.ui_updater, 'schedule_gui_task'):
                    self.ui_updater.schedule_gui_task(self.ui_updater.update_job_in_display, updated_job.id, new_status.value, old_status.value if old_status else None)
                 else: # 尽力而为
                    self.ui_updater.update_job_in_display(updated_job.id, new_status.value, old_status.value if old_status else None)

            return {"success": True, "job_id": updated_job.job_id, "new_status": new_status.value}
        else:
            self._log_to_ui(f"未能更新职位 PK_ID:{job_pk_id} 的状态。", "error")
            return {"success": False, "error": f"未能找到或更新职位 PK_ID:{job_pk_id}"}

    async def perform_standalone_match_async(self, job_description: str, resume_text: str, job_title: Optional[str] = None) -> dict:
        """(异步) 执行独立的简历匹配任务 (用于GUI上的即时匹配功能)"""
        ai_service = next((s for s in self.services if isinstance(s, AiAnalysisService)), None)
        if not ai_service:
            msg = "AI分析服务未初始化或不可用。"
            self._log_to_ui(msg, "error")
            return {"error": msg, "match_score": 0}

        if not hasattr(ai_service, 'analyze_single_match_async'):
            msg = "AI分析服务缺少 'analyze_single_match_async' 方法。"
            self._log_to_ui(msg, "error")
            return {"error": msg, "match_score": 0}

        self._log_to_ui(f"开始独立简历匹配，职位: {job_title or 'N/A'}", "info")
        try:
            # AiAnalysisService 需要一个方法来执行这个一次性分析
            # 这个方法内部会使用 AiAnalyzerCore
            result = await ai_service.analyze_single_match_async(job_description, resume_text, job_title)
            self._log_to_ui(f"独立简历匹配完成。得分: {result.get('match_score')}", "info")
            return result
        except Exception as e:
            self._log_to_ui(f"执行独立简历匹配时发生错误: {e}", "error")
            logger.error(f"执行独立简历匹配时发生错误: {e}", exc_info=True)
            return {"error": f"匹配执行错误: {str(e)}", "match_score": 0}


if __name__ == '__main__':
    # 简单的测试 AppController (需要一个模拟的Config和DBManager)
    # 这部分通常在集成测试中进行
    print("AppController 骨架，请在集成环境中测试。")

    # 模拟配置
    class MockConfig:
        def get(self, key, default=None):
            if key == 'common': return MockCommonConfig()
            if key == 'log': return {}
            if key == 'crawler': return {} # 返回爬虫配置字典
            return default
    class MockCommonConfig:
        database_uri = 'sqlite:///:memory:' # 使用内存数据库

    # 模拟DBManager
    mock_db_manager = DatabaseManager(MockConfig().common.database_uri)
    
    # 模拟UIUpdater
    class MockUiUpdater:
        def log(self, msg, lvl): print(f"[UI MOCK LOG - {lvl}]: {msg}")
        def schedule_gui_task(self, task, *args):
            print(f"[UI MOCK SCHEDULE]: {task.__name__} with {args}")
            task(*args)
        def update_job_in_display(self, job_id, new_status, old_status):
             print(f"[UI MOCK UPDATE]: Job {job_id} status from {old_status} to {new_status}")

    mock_ui_updater = MockUiUpdater()
    
    # 设置基本日志，以便能看到AppController的日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    try:
        controller = AppController(MockConfig(), mock_db_manager, mock_ui_updater)
        controller.start_all_services() # 会尝试启动 CrawlerService (目前是骨架)
        
        # 模拟异步任务提交
        async def sample_async_task():
            print("Sample async task is running...")
            await asyncio.sleep(0.1)
            print("Sample async task finished.")
            return "Task Done"

        def task_callback(result_or_exc):
            if isinstance(result_or_exc, Exception):
                print(f"Task callback received exception: {result_or_exc}")
            else:
                print(f"Task callback received result: {result_or_exc}")

        future = controller.submit_async_task(sample_async_task(), task_callback)
        if future:
            print(f"Submitted sample_async_task, future: {future}")
            # 在实际应用中，不会在这里 .result() 阻塞主线程
            # time.sleep(0.5) # 等待任务完成

        # 模拟手动更改状态 (需要先有职位在数据库中)
        # test_job = mock_db_manager.add_job({"job_id": "ctrl_test01", "job_title": "Controller Test Job", "source_platform":"Test", "source_url":"http://example.com"})
        # if test_job:
        #     async def change_status_coro():
        #         return await controller.manually_change_job_pipeline_status_async(test_job.id, JobStatus.USER_IGNORED, test_job.status)
        #     controller.submit_async_task(change_status_coro(), task_callback)
        #     time.sleep(0.2)


        print("AppController test running for 1 second...")
        threading.Event().wait(1) # 保持主线程存活一段时间，让后台线程运行

    except RuntimeError as e:
        print(f"Runtime error during AppController test: {e}")
    except Exception as e_main:
        print(f"General error during AppController test: {e_main}", exc_info=True)
    finally:
        if 'controller' in locals() and controller:
            print("Shutting down AppController...")
            controller.shutdown()
        if mock_db_manager:
            mock_db_manager.close()
        print("Test finished.")

