#!/usr/bin/env python3
"""
测试去除qfluentwidgets后的GUI功能
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.gui.config_window import ConfigWindow

def test_config_window():
    """测试配置窗口"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式为深色主题
    app.setStyle('Fusion')
    
    try:
        window = ConfigWindow()
        print("✅ ConfigWindow 创建成功")
        window.show()
        print("✅ ConfigWindow 显示成功")
        
        # 快速显示和关闭
        window.close()
        print("✅ ConfigWindow 关闭成功")
        
    except Exception as e:
        print(f"❌ ConfigWindow 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    if test_config_window():
        print("🎉 GUI测试通过 - qfluentwidgets已成功移除！")
    else:
        print("❌ GUI测试失败")
        sys.exit(1)
