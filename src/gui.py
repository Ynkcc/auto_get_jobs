import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import QThread, QObject, Signal, Slot

# --- 路径调整 ---
# 因为 gui.py 在 src 目录中，所以可以直接从同级模块导入
from .main import main as run_async_main
from .common.event_manager import event_manager

# --- 步骤 1: 创建一个 QThread 来运行 asyncio 事件循环 ---
class AsyncioThread(QThread):
    """
    该线程专门用于运行 asyncio 的事件循环和您的主程序。
    """
    def __init__(self):
        super().__init__()
        self.loop = None

    def run(self):
        # 在新线程中创建并运行事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(run_async_main())
    
    def stop(self):
        # 请求事件循环停止
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.quit()
        self.wait()


# --- 步骤 2: 创建一个通信对象，用于后台与GUI之间的信号传递 ---
class Communicator(QObject):
    # 使用 PySide6 的 Signal
    log_message = Signal(str)

    def __init__(self):
        super().__init__()

    # 使用 PySide6 的 Slot
    @Slot(str)
    def post_log(self, message):
        self.log_message.emit(message)

# --- 步骤 3: 创建主窗口 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bossbot 控制面板 (PySide6)")
        self.setGeometry(100, 100, 800, 600)

        # 创建UI组件
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.start_button = QPushButton("启动后台任务")
        self.start_button.clicked.connect(self.start_backend)
        
        self.custom_action_button = QPushButton("触发自定义事件 (示例)")
        self.custom_action_button.clicked.connect(self.trigger_custom_action)
        self.custom_action_button.setEnabled(False) # 初始不可用

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.custom_action_button)
        layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 初始化后台线程和通信
        self.asyncio_thread = AsyncioThread()
        self.communicator = Communicator()
        
        # 连接信号到槽，用于更新日志
        self.communicator.log_message.connect(self.update_log)

    def start_backend(self):
        """点击“启动”按钮后执行"""
        self.log_output.append("正在启动后台任务...")
        self.asyncio_thread.start()
        self.start_button.setEnabled(False)
        self.custom_action_button.setEnabled(True)
        self.log_output.append("后台任务已启动。")

    def trigger_custom_action(self):
        """点击“自定义事件”按钮后执行"""
        self.log_output.append("[GUI] 正在发布 'add_friend' 事件...")
        
        async def publish_event():
            # 这是一个示例，您需要提供真实的 job_data 和 greeting_message
            mock_job_data = {'jobInfo': {'jobName': '测试职位'}, 'bossInfo':{}, 'securityId': 'xxx'}
            await event_manager.publish("add_friend", job_data=mock_job_data, greeting_message="你好，这是一个来自GUI的测试消息")
        
        # 确保 asyncio_thread 已经启动并且 loop 已经创建
        if self.asyncio_thread.isRunning() and self.asyncio_thread.loop:
            asyncio.run_coroutine_threadsafe(publish_event(), self.asyncio_thread.loop)
        else:
            self.log_output.append("[错误] 后台任务未运行，无法发布事件。")

    # 使用 PySide6 的 Slot
    @Slot(str)
    def update_log(self, message):
        """安全地从任何线程更新日志文本框"""
        self.log_output.append(message)

    def closeEvent(self, event):
        """关闭窗口时，确保后台线程也停止"""
        self.log_output.append("正在关闭应用...")
        # 此处可以添加优雅停止的逻辑，例如通过 event_manager 发布一个 'shutdown' 事件
        # await event_manager.publish("shutdown")
        self.asyncio_thread.stop()
        event.accept()

def main():
    """
    GUI 应用的主入口函数
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 示例：订阅一个后台事件，并将其转发到GUI
    async def forward_log_to_gui(analysis_data: dict, **kwargs):
        is_match = analysis_data.get('is_match')
        job_name = analysis_data.get("job_info", {}).get("jobInfo", {}).get("jobName", "未知职位")
        log_msg = f"[后台] 分析完成: '{job_name}', 匹配结果: {is_match}"
        # 通过communicator将消息安全地发送到GUI线程
        window.communicator.post_log(log_msg)

    event_manager.subscribe("job_analysis_complete", forward_log_to_gui)

    window.show()
    return app.exec()

if __name__ == "__main__":
    # 如果直接运行此文件，也能够启动
    sys.exit(main())