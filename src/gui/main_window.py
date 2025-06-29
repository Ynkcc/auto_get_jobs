# src/gui.py
import sys
import asyncio
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                               QHBoxLayout, QVBoxLayout, QWidget, QGroupBox, QMessageBox)
from PySide6.QtCore import QThread, QObject, Signal, Slot, Qt
from PySide6.QtGui import QPalette, QColor

from ..main import main as run_async_main
from ..common.event_manager import event_manager
from .config_window import ConfigWindow
from ..common.config_manager import ConfigManager


class AsyncioThread(QThread):
    def __init__(self):
        super().__init__()
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        ConfigManager.load_config()
        # 创建主任务并在事件循环中运行
        self.loop.create_task(run_async_main())
        self.loop.run_forever()

    def stop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            while self.loop.is_running():
                self.msleep(100)
        self.quit()
        self.wait()


class Communicator(QObject):
    log_message = Signal(str)
    fetch_complete = Signal()
    # 新增信号，用于在后台登录成功后通知GUI
    login_successful = Signal()

    def __init__(self):
        super().__init__()

    @Slot(str)
    def post_log(self, message):
        self.log_message.emit(message)
    
    @Slot()
    def notify_fetch_complete(self):
        self.fetch_complete.emit()

    @Slot()
    def notify_login_success(self):
        self.login_successful.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bossbot 控制面板 (v2.0)")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化状态
        self.is_paused = False
        
        # 创建UI组件
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # --- 修改点 1: 创建登录和配置按钮 ---
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.start_backend_login)
        self.config_button = QPushButton("配置")
        self.config_button.clicked.connect(self.open_config_window)

        # --- 修改点 2: 创建任务控制按钮组 ---
        self.task_control_group = QGroupBox("任务控制")
        task_control_layout = QHBoxLayout()

        self.start_fetch_button = QPushButton("开始获取")
        self.start_fetch_button.clicked.connect(self.trigger_start_fetch)
        
        self.pause_fetch_button = QPushButton("暂停获取")
        self.pause_fetch_button.clicked.connect(self.toggle_pause_fetch)

        self.stop_fetch_button = QPushButton("停止获取")
        self.stop_fetch_button.clicked.connect(self.trigger_stop_fetch)
        
        task_control_layout.addWidget(self.start_fetch_button)
        task_control_layout.addWidget(self.pause_fetch_button)
        task_control_layout.addWidget(self.stop_fetch_button)
        self.task_control_group.setLayout(task_control_layout)
        
        # 初始时禁用任务控制按钮
        self.task_control_group.setEnabled(False)

        # --- 修改点 3: 设置新的布局 ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.login_button)
        top_layout.addWidget(self.config_button)
        top_layout.addStretch() # 添加伸缩，使按钮靠左

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.task_control_group) # 添加任务控制组
        main_layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- 修复: 在所有UI组件创建完成后设置主题 ---
        self.set_dark_theme()

        # 初始化后台线程和通信
        self.asyncio_thread = AsyncioThread()
        self.communicator = Communicator()

        # 连接信号到槽
        self.communicator.log_message.connect(self.update_log)
        self.communicator.fetch_complete.connect(self.on_fetch_complete)
        self.communicator.login_successful.connect(self.on_login_success)

    def set_dark_theme(self):
        """设置一个简单的暗色主题，美化UI"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        self.log_output.setStyleSheet("QTextEdit { background-color: #1E1E1E; color: #D4D4D4; }")


    def start_backend_login(self):
        """点击“登录”按钮后执行，取代旧的 start_backend"""
        if self.asyncio_thread.isRunning():
            self.update_log("[警告] 后台服务已在运行中。")
            return
        self.update_log("正在启动后台服务并尝试登录...")
        self.asyncio_thread.start()
        self.login_button.setEnabled(False)
        self.update_log("后台服务已启动。请在浏览器中完成扫码登录（如果需要）。")

    @Slot()
    def on_login_success(self):
        """登录成功后的回调"""
        self.update_log("[GUI] 登录成功！现在可以开始获取岗位。")
        self.task_control_group.setEnabled(True) # 启用任务控制按钮

    def open_config_window(self):
        try:
            ConfigManager.get_config()
        except RuntimeError:
            ConfigManager.load_config()
        self.config_win = ConfigWindow(self)
        self.config_win.exec()

    def trigger_start_fetch(self):
        self.update_log("[GUI] 正在请求获取网页岗位...")
        self.start_fetch_button.setEnabled(False)
        self.pause_fetch_button.setEnabled(True)
        
        async def publish_event():
            await event_manager.publish("fetch_jobs_requested")

        if self.asyncio_thread.isRunning() and self.asyncio_thread.loop:
            asyncio.run_coroutine_threadsafe(publish_event(), self.asyncio_thread.loop)
        else:
            self.update_log("[错误] 后台服务未运行，无法获取岗位。")
            self.start_fetch_button.setEnabled(True)

    def toggle_pause_fetch(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.update_log("[GUI] 正在请求暂停获取任务...")
            self.pause_fetch_button.setText("继续获取")
            event_name = "pause_fetch_requested"
        else:
            self.update_log("[GUI] 正在请求继续获取任务...")
            self.pause_fetch_button.setText("暂停获取")
            event_name = "resume_fetch_requested"
        
        async def publish_event():
            await event_manager.publish(event_name)

        if self.asyncio_thread.isRunning() and self.asyncio_thread.loop:
            asyncio.run_coroutine_threadsafe(publish_event(), self.asyncio_thread.loop)

    def trigger_stop_fetch(self):
        self.update_log("[GUI] 正在请求停止当前任务...")
        self.task_control_group.setEnabled(False) # 停止后禁用所有控制
        
        async def publish_event():
            await event_manager.publish("stop_fetch_requested")

        if self.asyncio_thread.isRunning() and self.asyncio_thread.loop:
            asyncio.run_coroutine_threadsafe(publish_event(), self.asyncio_thread.loop)

    @Slot()
    def on_fetch_complete(self):
        self.update_log("[GUI] 网页岗位获取任务已完成或停止。")
        self.start_fetch_button.setEnabled(True)
        self.pause_fetch_button.setEnabled(True)
        self.task_control_group.setEnabled(True)
        self.pause_fetch_button.setText("暂停获取")
        self.is_paused = False

    @Slot(str)
    def update_log(self, message):
        self.log_output.append(message)

    def closeEvent(self, event):
        self.update_log("正在关闭应用...")
        async def publish_shutdown():
            await event_manager.publish("shutdown")
        
        if self.asyncio_thread.isRunning() and self.asyncio_thread.loop:
             future = asyncio.run_coroutine_threadsafe(publish_shutdown(), self.asyncio_thread.loop)
             try:
                 future.result(timeout=5)
             except asyncio.TimeoutError:
                 self.update_log("[警告] 关闭事件发布超时。")

        self.asyncio_thread.stop()
        event.accept()

def main_gui(): # 重命名以避免与 src/main.py 中的 main 冲突
    try:
        ConfigManager.load_config()
    except Exception as e:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "启动错误", f"加载配置失败，程序无法启动。\n错误: {e}")
        return 1

    app = QApplication(sys.argv)
    window = MainWindow()

    # --- 事件转发 ---
    async def forward_log_to_gui(analysis_data: dict, **kwargs):
        is_match = analysis_data.get('is_match')
        job_name = analysis_data.get("job_info", {}).get("jobInfo", {}).get("jobName", "未知职位")
        log_msg = f"[后台] 分析完成: '{job_name}', 匹配结果: {is_match}"
        window.communicator.post_log(log_msg)

    async def forward_fetch_complete_to_gui(**kwargs):
        window.communicator.notify_fetch_complete()

    async def forward_login_success_to_gui(**kwargs):
        window.communicator.notify_login_success()

    event_manager.subscribe("job_analysis_complete", forward_log_to_gui)
    event_manager.subscribe("fetch_jobs_complete", forward_fetch_complete_to_gui)
    event_manager.subscribe("login_successful", forward_login_success_to_gui)

    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main_gui())