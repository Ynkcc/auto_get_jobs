#!/usr/bin/env python3
# demo_multiselect.py - 多选下拉框功能演示

"""
多选下拉框功能演示脚本

这个脚本演示了为BOSS直聘自动投简历项目实现的多选下拉框功能，
包含以下主要功能：
1. 多选下拉框组件（MultiSelectComboBox）
2. 带合并选项的多选组件（MultiSelectWithCombineWidget）
3. 配置模型更新（MultiSelectConfig）
4. URL构建逻辑更新
5. 配置文件迁移
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.common.config_manager import ConfigManager, MultiSelectConfig

def demo_config_structure():
    """演示新的配置结构"""
    print("🔧 配置结构演示")
    print("=" * 50)
    
    # 创建多选配置
    config = MultiSelectConfig(values=[104, 105], combine=True)
    print(f"📋 配置对象: {config}")
    print(f"📝 配置字典: {config.model_dump()}")
    
    # 默认配置
    default_config = MultiSelectConfig()
    print(f"🔄 默认配置: {default_config.model_dump()}")
    print()

def demo_url_building():
    """演示URL构建功能"""
    print("🌐 URL构建演示")
    print("=" * 50)
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        from src.common.file_utils import build_search_url
        
        print("🔍 当前配置:")
        print(f"  📍 城市: {config.job_search.city.values}")
        print(f"  🎯 关键词: {config.job_search.query}")
        print(f"  💼 经验要求: {config.job_search.experience.model_dump()}")
        print(f"  🎓 学历要求: {config.job_search.degree.model_dump()}")
        print()
        
        urls = build_search_url(config.job_search)
        
        print(f"📊 生成的URL数量: {len(urls)}")
        print("🔗 URL示例:")
        for i, url in enumerate(urls[:3]):
            print(f"  {i+1}. {url}")
        
        if len(urls) > 3:
            print(f"  ... 还有 {len(urls) - 3} 个URL")
        print()
        
    except Exception as e:
        print(f"❌ URL构建失败: {e}")
        print()

def demo_search_params():
    """演示搜索参数映射"""
    print("🔍 搜索参数映射演示")
    print("=" * 50)
    
    import json
    
    try:
        config_path = os.path.join('config', 'search_params_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            params_data = json.load(f)
        
        # 展示经验要求映射
        print("💼 经验要求映射:")
        for name, code in params_data.get('experience', {}).items():
            print(f"  '{name}' -> {code}")
        print()
        
        # 展示学历要求映射
        print("🎓 学历要求映射:")
        for name, code in params_data.get('degree', {}).items():
            print(f"  '{name}' -> {code}")
        print()
        
        # 展示薪资范围映射
        print("💰 薪资范围映射:")
        for name, code in params_data.get('salary', {}).items():
            print(f"  '{name}' -> {code}")
        print()
        
    except Exception as e:
        print(f"❌ 搜索参数加载失败: {e}")
        print()

def demo_combine_logic():
    """演示合并逻辑"""
    print("🔄 合并逻辑演示")
    print("=" * 50)
    
    # 演示合并开启的情况
    combine_on = MultiSelectConfig(values=[104, 105, 106], combine=True)
    print("✅ 合并开启:")
    print(f"  配置: {combine_on.model_dump()}")
    print(f"  URL参数: experience={','.join(map(str, combine_on.values))}")
    print()
    
    # 演示合并关闭的情况
    combine_off = MultiSelectConfig(values=[104, 105, 106], combine=False)
    print("❌ 合并关闭:")
    print(f"  配置: {combine_off.model_dump()}")
    print(f"  URL参数: 分别为 experience=104, experience=105, experience=106")
    print()

def demo_configuration_window():
    """演示配置窗口功能"""
    print("🖥️ 配置窗口功能演示")
    print("=" * 50)
    
    try:
        from src.gui.widgets import MultiSelectWithCombineWidget
        
        # 模拟参数
        experience_options = {
            "不限": 0,
            "在校生": 108,
            "应届生": 102,
            "经验不限": 101,
            "1年以内": 103,
            "1-3年": 104,
            "3-5年": 105,
            "5-10年": 106,
            "10年以上": 107
        }
        
        config_dict = {"values": [104, 105], "combine": True}
        
        print("🎨 多选组件功能:")
        print(f"  📋 可选项: {list(experience_options.keys())}")
        print(f"  ⚙️ 当前配置: {config_dict}")
        print(f"  🔧 组件类型: MultiSelectWithCombineWidget")
        print("  ✨ 功能特点:")
        print("    - 支持多选下拉框")
        print("    - 支持合并选项配置")
        print("    - 自动显示选中项目")
        print("    - 实时更新配置")
        print()
        
    except Exception as e:
        print(f"❌ 配置窗口演示失败: {e}")
        print()

def main():
    """主函数"""
    print("🎉 BOSS直聘自动投简历 - 多选下拉框功能演示")
    print("=" * 60)
    print()
    
    demo_config_structure()
    demo_search_params()
    demo_combine_logic()
    demo_url_building()
    demo_configuration_window()
    
    print("✅ 功能特点总结:")
    print("  🔸 支持多选下拉框，用户可以选择多个选项")
    print("  🔸 保留"是否合并为单次请求"配置选项")
    print("  🔸 自动将选中的选项转换为URL参数")
    print("  🔸 兼容现有配置文件，提供迁移工具")
    print("  🔸 现代化的GUI界面，基于QFluentWidgets")
    print()
    
    print("📚 使用说明:")
    print("  1. 运行migrate_config.py迁移现有配置文件")
    print("  2. 运行src.gui.main_window启动GUI界面")
    print("  3. 在"职位搜索"标签页中配置多选选项")
    print("  4. 保存配置后系统会自动重载")
    print()
    
    print("🚀 演示完成！")

if __name__ == "__main__":
    main()
