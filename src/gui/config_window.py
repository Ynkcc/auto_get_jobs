# src/gui/config_window.py
import sys
import json
import os
import asyncio
from copy import deepcopy
from typing import Any, List, Dict, Optional, Type

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QScrollArea, QFrame, QGroupBox, QDialog, QStackedWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (setTheme, Theme, SubtitleLabel, LineEdit, CheckBox, ComboBox,
                            TextEdit, SpinBox, DoubleSpinBox, PushButton, FluentIcon,
                            InfoBar, InfoBarPosition, StrongBodyLabel, BodyLabel,
                            TableWidget, TabBar, Dialog)

import yaml

from ..common.config_manager import ConfigManager, AppConfig, BaseModel, Field, AiProvider
from ..common.event_manager import event_manager
from ..services.ai_analyzer import AiAnalyzer
# 导入新的自定义组件
from .widgets import MultiSelectComboBox, MultiSelectWithCombineWidget


class ListEditWidget(QWidget):
    """用于编辑列表数据的自定义小部件"""
    valueChanged = Signal(list)

    def __init__(self, items: List = None, parent=None):
        super().__init__(parent)
        self.items = items or []
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮布局
        button_layout = QHBoxLayout()
        add_button = PushButton("添加", self, FluentIcon.ADD)
        add_button.clicked.connect(self.add_item)
        self.remove_button = PushButton("删除", self, FluentIcon.DELETE)
        self.remove_button.clicked.connect(self.remove_item)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["值"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        
        self.table.itemSelectionChanged.connect(self.update_button_states)
        self.refresh_table()
        self.update_button_states()

    def refresh_table(self):
        self.table.setRowCount(0)
        for item in self.items:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            item_widget = QTableWidgetItem(str(item))
            item_widget.setFlags(item_widget.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_position, 0, item_widget)
        
        # 连接编辑信号
        self.table.itemChanged.connect(self.on_item_changed)

    def update_button_states(self):
        has_selection = bool(self.table.selectedItems())
        self.remove_button.setEnabled(has_selection)

    def add_item(self):
        self.items.append("")
        self.refresh_table()
        # 选择新添加的行并进入编辑模式
        new_row = self.table.rowCount() - 1
        self.table.selectRow(new_row)
        self.table.editItem(self.table.item(new_row, 0))
        self.valueChanged.emit(self.value())

    def remove_item(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: 
            return
        
        del self.items[selected_row]
        self.refresh_table()
        self.valueChanged.emit(self.value())

    def on_item_changed(self, item):
        row = item.row()
        if 0 <= row < len(self.items):
            self.items[row] = item.text()
            self.valueChanged.emit(self.value())

    def value(self) -> List:
        return self.items.copy()

class AiProviderDialog(QDialog):
    """用于添加或编辑AiProvider的对话框"""
    def __init__(self, provider_data: Optional[AiProvider] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑AI服务商" if provider_data else "添加AI服务商")
        self.setMinimumSize(400, 300)
        self.provider = provider_data
        
        layout = QVBoxLayout(self)
        
        # 创建表单布局
        form_layout = QFormLayout()
        self.widgets: Dict[str, QWidget] = {}

        # 动态创建字段
        for field_name, field_info in AiProvider.model_fields.items():
            value = getattr(self.provider, field_name) if self.provider else field_info.default
            
            if field_name == "provider_type":
                widget = ComboBox()
                widget.addItems(["openai", "azure"])
                widget.setCurrentText(str(value) if value is not None else "openai")
            elif field_info.annotation is bool:
                widget = CheckBox()
                widget.setChecked(bool(value) if value is not None else False)
            elif field_info.annotation is int:
                widget = SpinBox()
                widget.setValue(int(value) if value is not None and value != field_info.default else 0)
            elif field_info.annotation is float:
                widget = DoubleSpinBox()
                widget.setValue(float(value) if value is not None and value != field_info.default else 0.0)
            else:
                widget = LineEdit()
                widget.setText(str(value) if value is not None and value != field_info.default else '')
            
            self.widgets[field_name] = widget
            form_layout.addRow(StrongBodyLabel(f"{field_info.description or field_name}:"), widget)
        
        layout.addLayout(form_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.ok_button = PushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def get_data(self) -> Optional[AiProvider]:
        try:
            data_dict = {}
            for name, widget in self.widgets.items():
                if isinstance(widget, (LineEdit, ComboBox)):
                    data_dict[name] = widget.text() if isinstance(widget, LineEdit) else widget.currentText()
                elif isinstance(widget, (SpinBox, DoubleSpinBox)):
                    data_dict[name] = widget.value()
                elif isinstance(widget, CheckBox):
                    data_dict[name] = widget.isChecked()
            return AiProvider(**data_dict)
        except Exception as e:
            InfoBar.error("错误", f"数据无效: {e}", duration=3000, parent=self)
            return None


class AiProvidersWidget(QWidget):
    """用于管理AiProvider列表的自定义小部件"""
    valueChanged = Signal(list)

    def __init__(self, providers: List[AiProvider] = None, parent=None):
        super().__init__(parent)
        self.providers = providers or []
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮布局
        button_layout = QHBoxLayout()
        add_button = PushButton("添加", self, FluentIcon.ADD)
        add_button.clicked.connect(self.add_provider)
        self.edit_button = PushButton("编辑", self, FluentIcon.EDIT)
        self.edit_button.clicked.connect(self.edit_provider)
        self.remove_button = PushButton("删除", self, FluentIcon.DELETE)
        self.remove_button.clicked.connect(self.remove_provider)
        self.test_button = PushButton("测试选中服务", self, FluentIcon.PLAY)
        self.test_button.clicked.connect(self.test_provider)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.test_button)
        main_layout.addLayout(button_layout)

        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "API类型", "模型"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        self.table.itemSelectionChanged.connect(self.update_button_states)
        self.refresh_table()
        self.update_button_states()

    def refresh_table(self):
        self.table.setRowCount(0)
        for provider in self.providers:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(provider.id))
            self.table.setItem(row_position, 1, QTableWidgetItem(provider.name))
            self.table.setItem(row_position, 2, QTableWidgetItem(provider.provider_type))
            self.table.setItem(row_position, 3, QTableWidgetItem(provider.model))

    def update_button_states(self):
        has_selection = bool(self.table.selectedItems())
        self.edit_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)
        self.test_button.setEnabled(has_selection)

    def add_provider(self):
        dialog = AiProviderDialog(parent=self)
        if dialog.exec():
            new_provider = dialog.get_data()
            if new_provider:
                # 检查ID是否唯一
                if any(p.id == new_provider.id for p in self.providers):
                    InfoBar.warning("警告", f"ID '{new_provider.id}' 已存在。", duration=3000, parent=self)
                    return
                self.providers.append(new_provider)
                self.refresh_table()
                self.valueChanged.emit(self.value())

    def edit_provider(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        
        provider_to_edit = self.providers[selected_row]
        dialog = AiProviderDialog(provider_to_edit, self)
        if dialog.exec():
            updated_provider = dialog.get_data()
            if updated_provider:
                # 如果ID被修改，需要检查唯一性
                if updated_provider.id != provider_to_edit.id and any(p.id == updated_provider.id for p in self.providers):
                     InfoBar.warning("警告", f"ID '{updated_provider.id}' 已存在。", duration=3000, parent=self)
                     return
                self.providers[selected_row] = updated_provider
                self.refresh_table()
                self.valueChanged.emit(self.value())

    def remove_provider(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        
        del self.providers[selected_row]
        self.refresh_table()
        self.valueChanged.emit(self.value())

    def test_provider(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        
        provider_to_test = self.providers[selected_row]
        
        # 使用一个临时的AiAnalyzer实例来测试
        analyzer = AiAnalyzer()
        
        # 异步运行测试
        async def run_test():
            success, message = await analyzer.test_provider(provider_to_test)
            if success:
                InfoBar.success("测试成功", f"服务商 '{provider_to_test.name}': {message}", duration=3000, position=InfoBarPosition.TOP, parent=self.window())
            else:
                InfoBar.error("测试失败", f"服务商 '{provider_to_test.name}': {message}", duration=-1, position=InfoBarPosition.TOP, parent=self.window())

        # 在现有的事件循环中安全地运行
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(run_test(), loop)
        else:
            loop.run_until_complete(run_test())

    def value(self) -> List[Dict]:
        # 返回字典列表以供序列化
        return [p.model_dump() for p in self.providers]


class ConfigWindow(QDialog):
    """一个基于数据驱动和Qt-Fluent-Widgets的现代化配置窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑配置")
        self.setMinimumSize(900, 750)

        self._load_meta_data()
        self.config_manager = ConfigManager()
        self.pydantic_model = self.config_manager.get_config()
        self.widgets_map: Dict[str, QWidget] = {}

        main_layout = QVBoxLayout(self)
        self.tab_widget = TabBar(self)
        self.stacked_widget = QStackedWidget(self)
        
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.stacked_widget, 1)

        self._create_tabs()
        
        # 连接标签切换
        self.tab_widget.currentChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self._create_buttons(main_layout)

    def _load_meta_data(self):
        self.search_params_meta = {}
        try:
            # 保证路径的正确性
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'config', 'search_params_config.json')
            if not os.path.exists(config_path):
                 config_path = "search_params_config.json" # Fallback for running from root
            with open(config_path, 'r', encoding='utf-8') as f:
                self.search_params_meta = json.load(f)
        except Exception as e:
            print(f"警告：加载搜索参数元数据失败: {e}")

    def _create_tabs(self):
        tab_order = ["ai", "job_search", "job_check", "application", "crawler", "accounts", "database", "logging", "notification", "ws_client"]
        model_fields = self.pydantic_model.model_fields

        for key in tab_order:
            if key in model_fields:
                field_info = model_fields[key]
                tab_name = field_info.description or key.replace("_", " ").title()
                
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setFrameShape(QFrame.Shape.NoFrame)
                
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                
                # 为该标签页的配置模型生成控件
                self._generate_widgets_for_model(
                    parent_layout=container_layout,
                    model=getattr(self.pydantic_model, key),
                    base_path=key
                )
                
                scroll_area.setWidget(container)
                self.stacked_widget.addWidget(scroll_area)
                self.tab_widget.addTab(key, tab_name, None)

    def _generate_widgets_for_model(self, parent_layout: QVBoxLayout, model, base_path: str):
        if not hasattr(model, 'model_fields'):
            return
            
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        for field_name, field_info in model.model_fields.items():
            current_path = f"{base_path}.{field_name}"
            current_value = getattr(model, field_name)
            
            # 特殊处理AI服务商列表
            if current_path == "ai.providers":
                widget = AiProvidersWidget(current_value)
                self.widgets_map[current_path] = widget
                # 将复杂控件添加到主布局而非表单布局
                parent_layout.addWidget(SubtitleLabel(field_info.description or field_name))
                parent_layout.addWidget(widget)
                continue

            # 检查是否为需要多选的字段 (MultiSelectConfig类型)
            multi_select_keys = ['experience', 'degree', 'salary', 'scale', 'stage', 'jobType']
            if field_name in multi_select_keys and field_name in self.search_params_meta:
                options = self.search_params_meta[field_name]
                # current_value应该是一个MultiSelectConfig对象
                if hasattr(current_value, 'model_dump'):  # 如果是Pydantic模型
                    config_dict = current_value.model_dump()
                elif isinstance(current_value, dict):
                    config_dict = current_value
                else:
                    # 兼容旧格式，如果是列表则转换为新格式
                    config_dict = {"values": current_value if isinstance(current_value, list) else [0], "combine": True}
                
                widget = MultiSelectWithCombineWidget(items=options, config_dict=config_dict)
                self.widgets_map[current_path] = widget
                parent_layout.addWidget(SubtitleLabel(field_info.description or field_name))
                parent_layout.addWidget(widget)
                continue

            if isinstance(current_value, BaseModel):
                group_box = QGroupBox(field_info.description or field_name.replace("_", " ").title())
                group_layout = QVBoxLayout(group_box)
                self._generate_widgets_for_model(group_layout, current_value, current_path)
                parent_layout.addWidget(group_box)
            else:
                label = StrongBodyLabel(f"{field_info.description or field_name.replace('_', ' ').title()}:")
                widget = self._create_widget(current_path, field_info, current_value)
                if widget:
                    self.widgets_map[current_path] = widget
                    form_layout.addRow(label, widget)

        parent_layout.addLayout(form_layout)

    def _create_widget(self, path: str, field_info: Field, value: Any) -> Optional[QWidget]:
        field_type = field_info.annotation
        
        json_key = path.split('.')[-1]
        
        # 检查是否为需要多选的字段 (包含values和combine的配置)
        multi_select_keys = ['experience', 'degree', 'salary', 'scale', 'stage', 'jobType']
        if json_key in multi_select_keys and json_key in self.search_params_meta:
            options = self.search_params_meta[json_key]
            # value应该是一个包含values和combine字段的字典
            if hasattr(value, 'model_dump'):  # 如果是Pydantic模型
                config_dict = value.model_dump()
            elif isinstance(value, dict):
                config_dict = value
            else:
                # 兼容旧格式，如果是列表则转换为新格式
                config_dict = {"values": value if isinstance(value, list) else [0], "combine": True}
            
            widget = MultiSelectWithCombineWidget(items=options, config_dict=config_dict)
            return widget

        # 首先检查是否为列表类型
        if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
             return ListEditWidget(value)
            
        # --- 更新：处理ComboBox的映射逻辑 ---
        if json_key in self.search_params_meta and isinstance(self.search_params_meta[json_key], dict):
            combo = ComboBox()
            options = self.search_params_meta[json_key]
            # 添加 item，将 code 存储在 UserRole 数据中
            for name, code in options.items():
                combo.addItem(name, userData=code)
            
            # 根据已保存的 code (value) 来设置当前选中的项
            # 查找 userData 等于 value 的索引
            index = combo.findData(value)
            if index != -1:
                combo.setCurrentIndex(index)
            return combo
            
        if field_type is bool:
            widget = CheckBox()
            widget.setChecked(bool(value))
            return widget
        if field_type is int:
            widget = SpinBox()
            widget.setRange(-2147483648, 2147483647)
            widget.setValue(value)
            return widget
        if field_type is float:
            widget = DoubleSpinBox()
            widget.setRange(-1e9, 1e9)
            widget.setValue(value)
            return widget
        if field_type is str:
            # 增加对密码字段的判断
            if 'password' in path or 'api_key' in path:
                widget = LineEdit()
                widget.setEchoMode(LineEdit.EchoMode.Password)
            elif 'file' in path or 'path' in path or 'prompt' in path or len(str(value)) > 80 :
                 widget = TextEdit()
                 widget.setPlainText(str(value))
                 widget.setMinimumHeight(150)
                 return widget
            else:
                widget = LineEdit()
            widget.setText(str(value))
            return widget
            
        return None

    def _create_buttons(self, layout: QVBoxLayout):
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.save_button = PushButton(FluentIcon.SAVE, "保存并重载")
        self.save_button.clicked.connect(self.save_config)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def save_config(self):
        try:
            # 使用深拷贝以避免修改原始模型实例
            updated_data = deepcopy(self.pydantic_model).model_dump()
            
            for path, widget in self.widgets_map.items():
                keys = path.split('.')
                data_level = updated_data
                for key in keys[:-1]:
                    data_level = data_level[key]
                
                last_key = keys[-1]
                value = None

                # --- 更新：获取控件值的逻辑 ---
                if isinstance(widget, ComboBox):
                    # 直接获取当前项关联的 userData (即 code)
                    value = widget.currentData()
                elif isinstance(widget, (MultiSelectWithCombineWidget, AiProvidersWidget, ListEditWidget)): 
                    value = widget.value()
                elif isinstance(widget, CheckBox): value = widget.isChecked()
                elif isinstance(widget, (SpinBox, DoubleSpinBox)): value = widget.value()
                elif isinstance(widget, TextEdit): value = widget.toPlainText()
                elif isinstance(widget, LineEdit): value = widget.text()
                
                if value is not None:
                    data_level[last_key] = value

            # 在保存前用新数据验证模型
            AppConfig(**updated_data)

            config_path = self.config_manager.get_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(updated_data, f, allow_unicode=True, sort_keys=False, indent=2)

            # 重新加载配置并发布事件
            self.config_manager.load_config(config_path)
            
            # 使用 run_coroutine_threadsafe 在GUI线程中安全地运行异步事件
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(event_manager.publish("config_reloaded"), loop)
            
            InfoBar.success("成功", "配置已成功保存并重载！", duration=3000, position=InfoBarPosition.TOP, parent=self)
            self.accept()
            
        except Exception as e:
            # 提供更详细的错误信息
            InfoBar.error("错误", f"保存配置失败: {e}", duration=-1, position=InfoBarPosition.TOP, parent=self)
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    # HiDPI settings
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    
    # 创建一个后台线程来运行事件循环
    loop = asyncio.new_event_loop()
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    import threading
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    # 在主线程中运行UI
    try:
        ConfigManager.load_config() 
    except Exception as e:
        print(f"加载初始配置失败: {e}")
        # 在GUI中显示错误
        error_dialog = Dialog("配置错误", f"加载初始配置失败: {e}")
        error_dialog.exec()
        sys.exit(1)
            
    window = ConfigWindow()
    window.show()
    
    app.exec()

    # 停止事件循环
    loop.call_soon_threadsafe(loop.stop)
    thread.join()