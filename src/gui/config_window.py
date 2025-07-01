# src/gui/config_window.py
import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox, QScrollArea, QDialog,
    QMessageBox, QTabWidget, QGroupBox, QTextEdit, QFrame, QComboBox,
    QCompleter
)
from PySide6.QtCore import Qt, QStringListModel
from ..common.config_manager import ConfigManager
from ..common.event_manager import event_manager
import yaml
import asyncio
from copy import deepcopy

class ConfigWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑配置")
        self.setMinimumSize(850, 700)

        # 翻译映射
        self.translation_map = {
            "ai": "AI 设置", "crawler": "爬虫设置", "application": "投递设置",
            "job_search": "职位搜索", "job_check": "职位筛选",
            "notification": "通知设置", "database": "数据库设置",
            "accounts": "账户设置", "logging": "日志设置", "ws_client": "WebSocket 设置",
            "playwright": "浏览器核心", "rate_limit": "请求速率限制", "greeting": "问候语设置",
            "exclude_keywords": "关键词排除", "email": "邮件通知", "webhook": "Webhook通知",
            "browser_type": "浏览器类型", "custom_browser_path": "自定义浏览器路径",
            "headless": "无头模式", "use_default_data_dir": "使用默认用户数据", "scroll_pages": "默认滚动页数",
            "rate": "速率 (次/秒)", "capacity": "容量", "next_page_delay": "翻页延迟 (秒)",
            "request_timeout": "请求超时 (秒)", "page_load_timeout": "页面加载超时 (秒)",
            "active_ai_id": "当前AI服务", "providers": "服务商列表", "prompt": "AI分析提示词",
            "job_requirements_prompt": "用户求职偏好", "resume_for_ai_file": "简历文件路径 (AI使用)",
            "send_resume_image": "发送简历图片", "resume_image_file": "简历图片文件",
            "enable_ai": "启用AI生成", "greeting_prompt": "问候语生成提示词",
            "greeting_for_ai_file": "问候语参考文件", "resume_name": "简历文件名称",
            "level": "日志级别", "path": "日志文件路径", "max_size": "最大文件大小 (MB)",
            "filename": "数据库文件", "export_excel": "运行后导出Excel", "excel_path": "Excel导出目录",
            "city": "目标城市", "query": "搜索关键词", "areas": "目标区域", "degree": "学历要求",
            "experience": "经验要求", "position": "岗位名称", "industry": "行业",
            "salary": "薪资过滤", "jobType": "工作类型", "scale": "公司规模", "stage": "融资阶段",
            "values": "值", "combine": "组合搜索", "expand_to_district": "展开到区域",
            "username": "用户名", "login_data_file": "登录数据文件",
            "test_mode": "测试模式 (只投不活跃HR)", "salary_range": "期望薪资范围 (千元)",
            "inactive_status": "排除不活跃HR状态", "check_insurance": "检查社保人数", "min_insured": "最小参保人数",
            "exclude_outsource": "排除外包公司", "check_visited": "检查已投递岗位",
        }

        self._load_search_params_meta()

        self.config = ConfigManager.get_config()
        self.config_data = self.config.model_dump()
        self.widgets = {}
        self.list_layouts = {}
        self.new_item_inputs = {}
        self.city_area_widgets = {}

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        # 修改点1: 还原翻页按钮
        self.tab_widget.setUsesScrollButtons(True)
        main_layout.addWidget(self.tab_widget)

        self._create_tabs()

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存并重载")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def _tr(self, text):
        return self.translation_map.get(text, text.replace("_", " ").title())

    def _load_search_params_meta(self):
        self.search_params_meta = {}
        try:
            config_path = "config/search_params_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.search_params_meta = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载搜索参数配置文件失败: {e}")

    def _create_tabs(self):
        tab_order = ["ai", "job_search", "job_check", "application", "crawler", "accounts", "database", "logging", "notification", "ws_client"]
        for key in tab_order:
            if key in self.config_data:
                tab_name = self._tr(key)
                if key in ['notification']: tab_name += " (部分未实现)"
                self._create_tab(tab_name, key)

    def _create_tab(self, tab_name: str, config_key: str):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignTop)
        
        data = self.config_data[config_key]
        if isinstance(data, list):
            self._create_list_group(container_layout, config_key, tab_name)
        elif isinstance(data, dict):
            if config_key == 'ai':
                self._create_ai_config_widgets(data, container_layout, config_key)
            else:
                self._create_widgets_for_dict(data, container_layout, config_key)
        
        scroll_area.setWidget(container_widget)
        self.tab_widget.addTab(scroll_area, tab_name)
    
    def _get_list_from_path(self, base_path):
        data_level = self._get_value_from_path(self.config_data, base_path.split('.'))
        if data_level is None: return None
        
        target_list = None
        if isinstance(data_level, list):
            target_list = data_level
        elif isinstance(data_level, dict) and 'values' in data_level:
            target_list = data_level.get('values', [])

        return target_list

    def _create_list_group(self, parent_layout, base_path: str, group_title: str):
        list_group_box = QGroupBox(self._tr(group_title))
        list_layout = QVBoxLayout(list_group_box)
        parent_layout.addWidget(list_group_box)
        self.list_layouts[base_path] = list_layout

        data_list = self._get_list_from_path(base_path)
        if data_list is not None:
            item_path_prefix = base_path if isinstance(data_list, list) else f"{base_path}.values"
            for index, item in enumerate(data_list):
                item_path = f"{item_path_prefix}.{index}"
                self._add_list_item_widget(list_layout, item, item_path, base_path)
        
        self._add_new_item_input_widget(list_layout, base_path)

    def _add_new_item_input_widget(self, list_layout, base_path):
        add_widget_layout = QHBoxLayout()
        key = base_path.split('.')[-1]
        
        if base_path.startswith("job_search.") and key in self.search_params_meta:
            input_widget = QComboBox()
            options = self.search_params_meta.get(key, {})
            for name in options.keys(): input_widget.addItem(name)
        else:
            input_widget = QLineEdit()
            if key == 'city' and self.search_params_meta.get("cityCode"):
                city_names = list(self.search_params_meta["cityCode"].keys())
                completer = QCompleter(city_names, self)
                input_widget.setCompleter(completer)
            elif key == 'areas':
                 self._update_area_completer()

        input_widget.setPlaceholderText("在此输入新条目")
        self.new_item_inputs[base_path] = input_widget
        add_widget_layout.addWidget(input_widget, 1)

        add_button = QPushButton("+")
        add_button.setFixedWidth(40)
        add_button.clicked.connect(lambda p=base_path: self._add_new_list_item(p))
        add_widget_layout.addWidget(add_button)
        list_layout.addLayout(add_widget_layout)
    
    def _create_ai_config_widgets(self, data, parent_layout, base_path):
        provider_layout = QHBoxLayout()
        provider_label = QLabel(self._tr("active_ai_id") + ":")
        provider_combo = QComboBox()
        
        self.ai_provider_tabs = QTabWidget()
        provider_combo.currentIndexChanged.connect(self.ai_provider_tabs.setCurrentIndex)

        self.widgets[f"{base_path}.active_ai_id"] = provider_combo
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(provider_combo, 1)

        add_provider_btn = QPushButton("+")
        add_provider_btn.setToolTip("添加一个新的AI服务商配置")
        add_provider_btn.clicked.connect(lambda: self._add_new_ai_provider(base_path))
        provider_layout.addWidget(add_provider_btn)

        parent_layout.addLayout(provider_layout)
        parent_layout.addWidget(self.ai_provider_tabs)

        self._redraw_ai_provider_tabs(base_path, data.get('active_ai_id'))
            
        other_ai_data = {k: v for k, v in data.items() if k not in ['providers', 'active_ai_id']}
        self._create_widgets_for_dict(other_ai_data, parent_layout, base_path)

    def _add_new_ai_provider(self, base_path):
        providers = self.config_data.get('ai', {}).get('providers', [])
        new_id = f"new_provider_{len(providers) + 1}"
        new_provider = {"id": new_id, "name": "新服务商", "provider": "openai", "model": "your-model", "api_key": "your-key", "api_url": "https://your-endpoint/v1", "temperature": 0.2, "api_version": ""}
        providers.append(new_provider)
        self.config_data['ai']['active_ai_id'] = new_id
        self._redraw_ai_provider_tabs(base_path, new_id)

    def _redraw_ai_provider_tabs(self, base_path, active_id=None):
        self.ai_provider_tabs.clear()
        combo = self.widgets.get(f"{base_path}.active_ai_id")
        if not combo: return
        
        try: combo.currentIndexChanged.disconnect()
        except RuntimeError: pass
        combo.clear()

        providers = self.config_data.get('ai', {}).get('providers', [])
        for index, provider_data in enumerate(providers):
            provider_path = f"{base_path}.providers.{index}"
            provider_tab = QWidget()
            provider_layout = QVBoxLayout(provider_tab)
            self._create_widgets_for_dict(provider_data, provider_layout, provider_path)
            tab_name = provider_data.get('name', f"Provider {index+1}")
            self.ai_provider_tabs.addTab(provider_tab, tab_name)
            combo.addItem(tab_name, provider_data.get('id'))

        if active_id:
            active_index = combo.findData(active_id)
            if active_index != -1:
                combo.setCurrentIndex(active_index)
                self.ai_provider_tabs.setCurrentIndex(active_index)
        combo.currentIndexChanged.connect(self.ai_provider_tabs.setCurrentIndex)
    
    def _create_widgets_for_dict(self, data: dict, parent_layout, base_path: str):
        unimplemented_fields = {"application.greeting.greeting_for_ai_file", "application.resume_name", "job_check.check_insurance", "job_check.min_insured", "job_check.exclude_outsource", "notification", "notification.email", "notification.webhook"}
        
        if base_path == "job_check" and "salary_range" in data:
            self._create_salary_range_widget(data['salary_range'], parent_layout, f"{base_path}.salary_range")

        for key, value in data.items():
            if base_path == "job_check" and key == "salary_range": continue
            current_path = f"{base_path}.{key}"
            
            # 使用 create_list_group 替代旧的逻辑
            if isinstance(value, list) or (base_path.startswith("job_search.") and key in ["city", "areas", "degree", "experience", "scale", "stage", "salary", "jobType"]):
                 self._create_list_group(parent_layout, current_path, key)
            elif isinstance(value, dict):
                group_box = QGroupBox(self._tr(key))
                group_layout = QVBoxLayout(group_box)
                if current_path in unimplemented_fields: group_box.setTitle(f"{group_box.title()} (未实现)")
                parent_layout.addWidget(group_box)
                self._create_widgets_for_dict(value, group_layout, current_path)
            else:
                item_layout = QHBoxLayout()
                label = QLabel(f"{self._tr(key)}:")
                if current_path in unimplemented_fields: label.setText(f"{label.text()} (未实现)")
                label.setFixedWidth(180)
                item_layout.addWidget(label)
                widget = None
                if isinstance(value, bool):
                    widget = QCheckBox(); widget.setChecked(value)
                elif key in ["prompt", "greeting_prompt", "job_requirements_prompt"]:
                    widget = QTextEdit(str(value)); widget.setMinimumHeight(150)
                else:
                    widget = QLineEdit(str(value))
                if widget:
                    item_layout.addWidget(widget, 1)
                    self.widgets[current_path] = widget
                parent_layout.addLayout(item_layout)
    
    def _create_salary_range_widget(self, value, parent_layout, base_path):
        layout = QHBoxLayout()
        label = QLabel(self._tr("salary_range") + ":")
        label.setFixedWidth(180)
        min_salary = QLineEdit(str(value[0]) if value and len(value) > 0 else "")
        max_salary = QLineEdit(str(value[1]) if value and len(value) > 1 else "")
        self.widgets[f"{base_path}.0"] = min_salary
        self.widgets[f"{base_path}.1"] = max_salary
        layout.addWidget(label)
        layout.addWidget(min_salary)
        layout.addWidget(QLabel("到"))
        layout.addWidget(max_salary)
        layout.addWidget(QLabel("K"))
        parent_layout.addLayout(layout)

    def _update_area_completer(self):
        area_input = self.new_item_inputs.get("job_search.areas")
        if not area_input: return
        current_cities = self._get_list_from_path("job_search.city") or []
        all_area_names = []
        for city_name in current_cities:
            city_data = self.search_params_meta.get("cityCode", {}).get(city_name, {})
            if city_data:
                first_city_code = next(iter(city_data))
                all_area_names.extend(list(city_data[first_city_code].keys()))
        unique_area_names = sorted(list(set(all_area_names)))
        model = QStringListModel(unique_area_names)
        completer = QCompleter(model, self)
        area_input.setCompleter(completer)

    # 修改点2/3: 极简的添加UI逻辑
    def _add_list_item_widget(self, list_layout, item_data, item_path, base_path):
        item_frame = QFrame()
        item_frame.setFrameShape(QFrame.StyledPanel)
        item_layout = QHBoxLayout(item_frame)
        if isinstance(item_data, dict):
            index = int(item_path.split('.')[-1])
            dict_group = QGroupBox(f"条目 #{index + 1}")
            dict_layout = QVBoxLayout(dict_group)
            self._create_widgets_for_dict(item_data, dict_layout, item_path)
            item_layout.addWidget(dict_group)
        else:
            widget = QLineEdit(str(item_data)); widget.setReadOnly(True)
            self.widgets[item_path] = widget
            item_layout.addWidget(widget)

        remove_button = QPushButton("-")
        remove_button.setFixedWidth(40)
        remove_button.clicked.connect(lambda f=item_frame: self._remove_list_item(base_path, f))
        item_layout.addWidget(remove_button)
        list_layout.insertWidget(list_layout.count() - 1, item_frame)
    
    # 修改点2/3: 修复并简化的添加数据逻辑
    def _add_new_list_item(self, path: str):
        input_widget = self.new_item_inputs.get(path)
        if not input_widget: return
        
        new_value = input_widget.currentText() if isinstance(input_widget, QComboBox) else input_widget.text().strip()
        if not new_value:
            QMessageBox.warning(self, "提示", "输入内容不能为空！")
            return
            
        target_list = self._get_list_from_path(path)
        if target_list is None:
             QMessageBox.critical(self, "错误", f"无法在路径 {path} 找到可添加的目标列表。")
             return

        if new_value in target_list:
            QMessageBox.information(self, "提示", f"'{new_value}' 已存在于列表中。")
            return
            
        # 1. 更新数据模型
        target_list.append(new_value)
        # 2. 更新UI
        list_layout = self.list_layouts[path]
        item_path_prefix = path if isinstance(target_list, list) else f"{path}.values"
        item_path = f"{item_path_prefix}.{len(target_list) - 1}"
        self._add_list_item_widget(list_layout, new_value, item_path, path)
        
        if isinstance(input_widget, QLineEdit): input_widget.clear()
        if path == 'job_search.city': self._update_area_completer()

    # 修改点2/3: 修复并简化的删除逻辑
    def _remove_list_item(self, base_path: str, item_frame: QFrame):
        list_layout = self.list_layouts.get(base_path)
        if not list_layout: return

        index_to_remove = -1
        for i in range(list_layout.count() - 1):
             if list_layout.itemAt(i).widget() == item_frame:
                 index_to_remove = i
                 break
        if index_to_remove == -1: return

        target_list = self._get_list_from_path(base_path)
        if target_list is not None and 0 <= index_to_remove < len(target_list):
             # 1. 更新数据模型
             del target_list[index_to_remove]
             # 2. 更新UI
             item_frame.deleteLater()
        
        if base_path == 'job_search.city': self._update_area_completer()

    def save_config(self):
        try:
            updated_data = deepcopy(self.config_data)
            for path, widget in self.widgets.items():
                keys = path.split('.')
                data_level = self._get_value_from_path(updated_data, keys[:-1])
                if data_level is None: continue
                last_key = keys[-1]
                original_value = self._get_value_from_path(self.config_data, keys)
                value = None
                if isinstance(widget, QCheckBox): value = widget.isChecked()
                elif isinstance(widget, QTextEdit): value = widget.toPlainText()
                elif isinstance(widget, QComboBox): value = widget.currentData()
                elif isinstance(widget, QLineEdit):
                    value = self._convert_to_original_type(widget.text(), original_value)
                if value is not None:
                    if last_key.isdigit():
                        if int(last_key) < len(data_level): data_level[int(last_key)] = value
                    else:
                        data_level[last_key] = value

            config_path = ConfigManager.get_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(updated_data, f, allow_unicode=True, sort_keys=False, indent=2)

            ConfigManager.load_config(config_path)
            asyncio.run(event_manager.publish("config_reloaded"))
            QMessageBox.information(self, "成功", "配置已成功保存并重载！")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _get_value_from_path(self, data, path_keys):
        temp_data = data
        for key in path_keys:
            try:
                if isinstance(temp_data, list) and key.isdigit():
                    temp_data = temp_data[int(key)]
                elif isinstance(temp_data, dict):
                    temp_data = temp_data[key]
                else: return None
            except (KeyError, IndexError): return None
        return temp_data

    def _convert_to_original_type(self, text, original_value):
        if text == '' and original_value is not None:
            if isinstance(original_value, (int, float)): return type(original_value)()
            return text
        if isinstance(original_value, bool): return text.lower() in ['true', '1', 't', 'y', 'yes']
        if isinstance(original_value, int):
            try: return int(text)
            except (ValueError, TypeError): return 0
        if isinstance(original_value, float):
            try: return float(text)
            except (ValueError, TypeError): return 0.0
        return text

if __name__ == '__main__':
    try:
        ConfigManager.load_config() 
    except Exception as e:
        QMessageBox.critical(None, "启动错误", f"加载初始配置失败: {e}")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())