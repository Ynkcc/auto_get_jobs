# src/config_window.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox, QScrollArea, QDialog,
    QMessageBox
)
from PySide6.QtCore import Qt
from ..common.config_manager import ConfigManager
import yaml
from collections.abc import MutableMapping

class ConfigWindow(QDialog):
    """
    一个用于编辑配置的对话框窗口。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑配置")
        self.setMinimumSize(600, 500)

        # 加载当前配置
        self.config = ConfigManager.get_config()
        self.config_data = self.config.model_dump()

        # 主布局
        main_layout = QVBoxLayout(self)

        # 滚动区域
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # 内容窗口
        self.content_widget = QWidget()
        scroll_area.setWidget(self.content_widget)
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setAlignment(Qt.AlignTop)

        # 动态创建UI
        self._create_widgets_for_level(self.config_data, self.layout)

        # 按钮
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

    def _create_widgets_for_level(self, data, layout):
        """
        递归地为配置数据的每一层创建控件。
        """
        for key, value in data.items():
            # 创建标签
            label = QLabel(f"<b>{key}</b>")
            layout.addWidget(label)

            # 根据值的类型创建不同的控件
            if isinstance(value, dict):
                # 为字典创建一个新的水平布局
                group_layout = QHBoxLayout()
                group_widget = QWidget()
                group_widget.setLayout(group_layout)
                nested_layout = QVBoxLayout()
                group_layout.addLayout(nested_layout)
                self._create_widgets_for_level(value, nested_layout)
                layout.addWidget(group_widget)
            elif isinstance(value, bool):
                # 为布尔值创建复选框
                checkbox = QCheckBox()
                checkbox.setChecked(value)
                layout.addWidget(checkbox)
                self.content_widget.setProperty(self._get_widget_key(layout, key), checkbox)
            elif isinstance(value, list):
                # 为列表创建多个行编辑器
                 list_layout = QVBoxLayout()
                 for i, item in enumerate(value):
                     list_item_layout = QHBoxLayout()
                     item_label = QLabel(f"  - Item {i+1}:")
                     line_edit = QLineEdit(str(item))
                     list_item_layout.addWidget(item_label)
                     list_item_layout.addWidget(line_edit)
                     list_layout.addLayout(list_item_layout)
                     self.content_widget.setProperty(self._get_widget_key(layout, f"{key}_{i}"), line_edit)
                 layout.addLayout(list_layout)

            else:
                # 为其他类型（字符串、数字等）创建行编辑器
                line_edit = QLineEdit(str(value))
                layout.addWidget(line_edit)
                self.content_widget.setProperty(self._get_widget_key(layout, key), line_edit)

    def _get_widget_key(self, layout, key):
        """生成一个唯一的键来存储和检索控件"""
        return f"{id(layout)}_{key}"

    def save_config(self):
        """
        保存配置。
        """
        try:
            updated_data = self._get_data_from_widgets(self.config_data, self.layout)
            ConfigManager.save_config(updated_data)
            QMessageBox.information(self, "成功", "配置已成功保存！")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _get_data_from_widgets(self, data, layout):
        """
        从UI控件中递归地收集数据。
        """
        updated_data = {}
        for key, value in data.items():
            widget_key = self._get_widget_key(layout, key)
            if isinstance(value, dict):
                 # 对于字典，我们需要找到其对应的布局并递归
                 # 注意：这里的实现需要简化，以便能正确找到嵌套的布局
                 # 在这个简化版本中，我们假设布局是直接嵌套的
                 # 在更复杂的UI中，可能需要更强大的控件<->数据映射
                 nested_layout = None
                 # 查找与此字典关联的布局
                 for i in range(layout.count()):
                     item = layout.itemAt(i)
                     if isinstance(item, QHBoxLayout) and item.itemAt(0) and isinstance(item.itemAt(0), QVBoxLayout):
                          # 这是一个简化的假设
                          nested_layout = item.itemAt(0)
                          break
                 if nested_layout:
                    updated_data[key] = self._get_data_from_widgets(value, nested_layout)
                 else:
                    updated_data[key] = value # 未找到则保持原样
            elif isinstance(value, bool):
                checkbox = self.content_widget.property(widget_key)
                updated_data[key] = checkbox.isChecked()
            elif isinstance(value, list):
                updated_list = []
                for i in range(len(value)):
                    item_widget_key = self._get_widget_key(layout, f"{key}_{i}")
                    line_edit = self.content_widget.property(item_widget_key)
                    updated_list.append(self._convert_to_original_type(line_edit.text(), value[i]))
                updated_data[key] = updated_list
            else:
                line_edit = self.content_widget.property(widget_key)
                updated_data[key] = self._convert_to_original_type(line_edit.text(), value)
        return updated_data

    def _convert_to_original_type(self, text, original_value):
        """尝试将文本转换回其原始数据类型"""
        if isinstance(original_value, int):
            return int(text)
        if isinstance(original_value, float):
            return float(text)
        return text

if __name__ == '__main__':
    # 示例用法
    ConfigManager.load_config("config/config.yaml") # 确保在创建窗口前加载配置
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())