from PySide6.QtWidgets import (
    QApplication, QMainWindow, QProgressBar, QLabel, QVBoxLayout, QWidget,
    QPushButton, QTextEdit
)
from PySide6.QtCore import QThread, Signal, Slot
import time
import random

# ==============================
# 多线程工作器
# ==============================
class CrawlerWorker(QThread):
    # 自定义信号（进度更新、消息日志、完成通知）
    progress_updated = Signal(int, str)  # (进度百分比, 当前任务状态)
    log_message = Signal(str)            # 日志信息
    finished = Signal()                  # 任务完成信号

    def __init__(self, total_tasks=100):
        super().__init__()
        self.total_tasks = total_tasks
        self._is_running = True

    def run(self):
        """模拟爬虫任务"""
        for i in range(1, self.total_tasks + 1):
            if not self._is_running:
                break

            # 模拟任务执行
            time.sleep(random.uniform(0.1, 0.5))
            status = f"正在抓取第 {i}/{self.total_tasks} 条数据..."
            
            # 发送信号更新UI
            self.progress_updated.emit(
                int((i/self.total_tasks)*100),
                status
            )
            self.log_message.emit(f"已完成: example.com/item/{i}")
        
        self.finished.emit()

    def stop(self):
        """安全停止任务"""
        self._is_running = False

# ==============================
# 主界面
# ==============================
class CrawlerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        """初始化界面组件"""
        # 主要组件
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("准备就绪")
        self.log_view = QTextEdit()
        self.start_btn = QPushButton("开始任务")
        self.stop_btn = QPushButton("停止任务")

        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_view)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 信号连接
        self.start_btn.clicked.connect(self.start_crawler)
        self.stop_btn.clicked.connect(self.stop_crawler)

    # ==============================
    # 核心逻辑
    # ==============================
    @Slot()
    def start_crawler(self):
        """启动爬虫任务"""
        if self.worker and self.worker.isRunning():
            return

        self.worker = CrawlerWorker(total_tasks=50)
        
        # 连接信号
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.add_log)
        self.worker.finished.connect(self.task_finished)
        
        self.worker.start()
        self.status_label.setText("任务进行中...")

    @Slot()
    def stop_crawler(self):
        """停止任务"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("已手动停止")

    @Slot(int, str)
    def update_progress(self, percent, status):
        """更新进度显示"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(status)

    @Slot(str)
    def add_log(self, message):
        """添加日志记录"""
        self.log_view.append(f"[{time.strftime('%H:%M:%S')}] {message}")

    @Slot()
    def task_finished(self):
        """任务完成处理"""
        self.status_label.setText("任务完成")
        self.progress_bar.setValue(100)

# ==============================
# 启动应用
# ==============================
if __name__ == "__main__":
    app = QApplication([])
    window = CrawlerGUI()
    window.setWindowTitle("爬虫进度监控 v1.0")
    window.resize(600, 400)
    window.show()
    app.exec()
