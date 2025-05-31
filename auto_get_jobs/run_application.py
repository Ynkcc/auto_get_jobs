# run_application.py (新的应用主入口)
import logging
import sys
import signal # 用于捕获终止信号

# 假设的GUI库导入，例如PyQt5
# from PyQt5.QtWidgets import QApplication
# from ui.main_window import MainWindow # 假设你的主窗口类

from app_core.utils.config_manager import ConfigManager
from app_core.utils.logging_config import setup_logging
from app_core.app_controller import AppController
from app_core.db.database_manager import DatabaseManager # 如果AppController不自己创建

# --- 全局变量 ---
app_controller_instance: AppController = None
# gui_application_instance = None # 如果需要全局访问GUI应用实例

def signal_handler(signum, frame):
    """
    捕获终止信号 (如 Ctrl+C) 并尝试优雅地关闭应用。
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"接收到信号 {signal.Signals(signum).name} ({signum})。正在尝试优雅关闭...")
    
    if app_controller_instance:
        logger.info("正在请求 AppController 停止处理...")
        app_controller_instance.stop_processing() # 假设 AppController 有 stop_processing 方法
    
    # if gui_application_instance and hasattr(gui_application_instance, 'quit'):
    #     logger.info("正在退出GUI应用...")
    #     gui_application_instance.quit()
        
    # 等待一段时间确保清理完成 (可选)
    # import time
    # time.sleep(2) 

    logger.info("应用程序退出。")
    sys.exit(0)

def main():
    """
    应用程序主入口函数。
    """
    # 1. 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # kill 命令

    # 2. 加载配置
    #   TODO: 允许通过命令行参数指定配置文件路径
    config_path = 'config/config.yaml' 
    try:
        config = ConfigManager.load_config(config_path)
    except FileNotFoundError:
        print(f"错误: 配置文件 '{config_path}' 未找到。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"加载配置文件 '{config_path}' 时出错: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. 设置日志
    setup_logging(config.get('log', {})) # 从配置中获取日志设置
    logger = logging.getLogger(__name__) # 在日志配置后获取logger
    logger.info(f"配置文件 '{config_path}' 已成功加载。")
    logger.info(f"应用启动，版本: {config.get('common', {}).get('version', 'N/A')}")

    # 4. 初始化数据库管理器 (如果 AppController 不自己处理)
    #    或者将config.common.database_uri传递给AppController让其内部创建
    db_manager = None
    try:
        db_manager = DatabaseManager(config.common.database_uri)
    except Exception as e:
        logger.critical(f"无法初始化数据库管理器: {e}. 应用将退出。", exc_info=True)
        sys.exit(1)
    
    # 5. 初始化 AppController
    global app_controller_instance
    try:
        # ui_updater 将是GUI主窗口的一个实例或一个专门的GUI更新处理类
        # 现在暂时设为None，或者创建一个简单的命令行版本
        class ConsoleUiUpdater: # 简易的命令行UI更新器 (用于测试)
            def log(self, message, level="info"):
                print(f"[GUI LOG - {level.upper()}]: {message}")
            def update_status(self, status_message):
                print(f"[GUI STATUS]: {status_message}")
            def schedule_gui_task(self, callable_task, *args): # 模拟GUI线程调度
                logger.debug(f"模拟GUI调度任务: {callable_task.__name__} 带参数 {args}")
                try:
                    callable_task(*args)
                except Exception as e_cb:
                    logger.error(f"ConsoleUiUpdater 执行回调任务时出错: {e_cb}", exc_info=True)


        ui_updater_instance = ConsoleUiUpdater() # 替换为真实的GUI更新器
        
        app_controller_instance = AppController(config, db_manager, ui_updater_instance)
        logger.info("AppController 已成功初始化。")
    except Exception as e:
        logger.critical(f"AppController 初始化失败: {e}. 应用将退出。", exc_info=True)
        if db_manager:
            db_manager.close()
        sys.exit(1)

    # 6. 初始化并运行GUI (或命令行交互)
    try:
        logger.info("正在启动用户界面...")
        # --- 替换为真实的GUI启动代码 ---
        # global gui_application_instance
        # gui_application_instance = QApplication(sys.argv)
        # main_window = MainWindow(app_controller_instance) # 将AppController注入GUI
        # # 将main_window或其一部分作为ui_updater连接到app_controller_instance (如果在AppController初始化时未传入)
        # # app_controller_instance.set_ui_updater(main_window.get_ui_updater_interface())
        # main_window.show()
        # exit_code = gui_application_instance.exec_()
        # --- 结束GUI启动代码 ---
        
        # --- 临时的命令行交互模式 (如果GUI未实现) ---
        logger.warning("GUI部分未实现或被注释。将进入命令行交互模式。")
        app_controller_instance.start_all_services() # 假设有此方法启动后台服务

        while True:
            cmd = input("输入 'stop' 停止服务, 'exit' 退出应用, 'status' 查看服务状态: ").strip().lower()
            if cmd == 'stop':
                app_controller_instance.stop_all_services() # 假设有此方法
                logger.info("所有服务已请求停止。")
            elif cmd == 'status':
                # 这里可以调用AppController的方法来获取服务状态并打印
                logger.info("服务状态查询功能未实现。")
                if app_controller_instance.is_any_service_running(): # 假设有此方法
                     logger.info("至少有一个服务正在运行。")
                else:
                     logger.info("所有服务都已停止或未启动。")
            elif cmd == 'exit':
                break
            else:
                logger.info(f"未知命令: {cmd}")
        
        exit_code = 0
        # --- 结束命令行交互 ---

        logger.info(f"用户界面已关闭，退出码: {exit_code}")

    except Exception as e:
        logger.critical(f"运行用户界面时发生严重错误: {e}", exc_info=True)
        exit_code = 1
    finally:
        logger.info("开始应用关闭前的清理工作...")
        if app_controller_instance:
            app_controller_instance.shutdown() # 确保AppController有shutdown方法进行彻底清理
        if db_manager:
            db_manager.close()
        logger.info("清理完成。应用程序即将退出。")
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
