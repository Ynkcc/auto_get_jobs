# src/gui/widgets.py
from typing import List, Dict, Any

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QDialog,
                               QListWidget, QListWidgetItem, QCheckBox, QHBoxLayout)

from qfluentwidgets import ComboBox, FluentIcon, CheckBox as FluentCheckBox

class MultiSelectComboBox(QPushButton):
    """
    一个支持多选的下拉框组件。
    """
    valueChanged = Signal(list)

    def __init__(self, items: Dict[str, Any], selected_codes: List[Any] = None, parent=None):
        """
        初始化多选下拉框。

        Args:
            items (Dict[str, Any]): 所有可选项，格式为 {显示文本: 实际值/代码}.
            selected_codes (List[Any], optional): 默认选中的值的列表. Defaults to None.
            parent (_type_, optional): 父组件. Defaults to None.
        """
        super().__init__(parent)
        self.items = items
        self.selected_codes = selected_codes if selected_codes is not None else []

        self.setIcon(FluentIcon.FILTER.icon())
        self._update_button_text()

        self.clicked.connect(self._show_popup)

    def _show_popup(self):
        popup = QDialog(self)
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(popup)
        list_widget = QListWidget(popup)
        layout.addWidget(list_widget)

        for text, code in self.items.items():
            item = QListWidgetItem(list_widget)
            checkbox = QCheckBox(text, list_widget)
            checkbox.setChecked(code in self.selected_codes)
            
            # 将代码与复选框关联
            checkbox.setProperty("item_code", code)
            checkbox.stateChanged.connect(self._on_selection_changed)

            list_widget.addItem(item)
            list_widget.setItemWidget(item, checkbox)
        
        # 定位和显示
        pos = self.mapToGlobal(QPoint(0, self.height()))
        popup.move(pos)
        popup.exec_()
    
    def _on_selection_changed(self, state: int):
        checkbox = self.sender()
        code = checkbox.property("item_code")

        if state == Qt.CheckState.Checked.value and code not in self.selected_codes:
            self.selected_codes.append(code)
        elif state == Qt.CheckState.Unchecked.value and code in self.selected_codes:
            self.selected_codes.remove(code)
        
        self._update_button_text()
        self.valueChanged.emit(self.value())

    def _update_button_text(self):
        if not self.selected_codes:
            self.setText("未选择")
            return
        
        # 显示选中的描述文本
        selected_texts = [text for text, code in self.items.items() if code in self.selected_codes]
        
        if len(selected_texts) > 2:
            display_text = f"{', '.join(selected_texts[:2])} 等{len(selected_texts)}项"
        else:
            display_text = ", ".join(selected_texts)
        self.setText(display_text)

    def value(self) -> List[Any]:
        """返回当前选中的代码列表"""
        return self.selected_codes

    def setValue(self, codes: List[Any]):
        """设置选中的代码列表"""
        self.selected_codes = codes
        self._update_button_text()
        self.valueChanged.emit(self.value())


class MultiSelectWithCombineWidget(QWidget):
    """
    支持多选和合并选项的组件
    """
    valueChanged = Signal(dict)

    def __init__(self, items: Dict[str, Any], config_dict: Dict = None, parent=None):
        """
        初始化多选组件，包含合并选项
        
        Args:
            items: 可选项字典 {显示文本: 代码值}
            config_dict: 配置字典，包含values和combine字段
        """
        super().__init__(parent)
        self.items = items
        
        # 设置默认值
        if config_dict is None:
            config_dict = {"values": [0], "combine": True}
        
        self.current_config = config_dict.copy()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 多选下拉框
        self.multi_select = MultiSelectComboBox(items, self.current_config.get("values", []))
        self.multi_select.valueChanged.connect(self._on_values_changed)
        layout.addWidget(self.multi_select)
        
        # 合并选项复选框
        self.combine_checkbox = FluentCheckBox("合并为单次请求")
        self.combine_checkbox.setChecked(self.current_config.get("combine", True))
        self.combine_checkbox.toggled.connect(self._on_combine_changed)
        layout.addWidget(self.combine_checkbox)

    def _on_values_changed(self, values: List[Any]):
        self.current_config["values"] = values
        self.valueChanged.emit(self.value())

    def _on_combine_changed(self, combine: bool):
        self.current_config["combine"] = combine
        self.valueChanged.emit(self.value())

    def value(self) -> Dict:
        """返回当前配置字典"""
        return self.current_config.copy()

    def setValue(self, config_dict: Dict):
        """设置配置值"""
        self.current_config = config_dict.copy()
        self.multi_select.setValue(config_dict.get("values", []))
        self.combine_checkbox.setChecked(config_dict.get("combine", True))
