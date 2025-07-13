#!/usr/bin/env python3
# test_multiselect.py - 测试多选下拉框功能

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.common.config_manager import ConfigManager, MultiSelectConfig

def test_config_structure():
    """测试新的配置结构"""
    print("=== 测试新的配置结构 ===")
    
    # 创建一个多选配置实例
    config = MultiSelectConfig(values=[104, 105], combine=True)
    print(f"配置对象: {config}")
    print(f"配置字典: {config.model_dump()}")
    
    # 测试默认值
    default_config = MultiSelectConfig()
    print(f"默认配置: {default_config.model_dump()}")
    print()

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"配置加载成功")
        print(f"job_search.experience: {config.job_search.experience}")
        print(f"job_search.degree: {config.job_search.degree}")
        print(f"job_search.salary: {config.job_search.salary}")
        print()
        
        return config
        
    except Exception as e:
        print(f"配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_url_building(config):
    """测试URL构建逻辑"""
    print("=== 测试URL构建逻辑 ===")
    
    if not config:
        print("配置为空，跳过URL构建测试")
        return
    
    try:
        from src.common.file_utils import build_search_url
        
        urls = build_search_url(config.job_search)
        
        print(f"生成的URL数量: {len(urls)}")
        for i, url in enumerate(urls[:3]):  # 只显示前3个
            print(f"URL {i+1}: {url}")
        
        if len(urls) > 3:
            print(f"... 还有 {len(urls) - 3} 个URL")
        print()
            
    except Exception as e:
        print(f"URL构建测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_widget_creation():
    """测试多选组件创建"""
    print("=== 测试多选组件创建 ===")
    
    try:
        from src.gui.widgets import MultiSelectWithCombineWidget
        
        # 模拟搜索参数
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
        
        # 创建配置
        config_dict = {"values": [104, 105], "combine": True}
        
        # 这里只是测试创建，不运行GUI
        print("多选组件创建测试：准备创建MultiSelectWithCombineWidget...")
        print(f"选项: {experience_options}")
        print(f"配置: {config_dict}")
        print("组件创建测试完成（未实际创建GUI）")
        print()
        
    except Exception as e:
        print(f"组件创建测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_config_save():
    """测试配置保存"""
    print("=== 测试配置保存格式 ===")
    
    try:
        # 创建一个测试配置
        test_config = MultiSelectConfig(values=[104, 105], combine=True)
        config_dict = test_config.model_dump()
        
        import yaml
        yaml_output = yaml.dump(config_dict, allow_unicode=True, sort_keys=False, indent=2)
        print("配置保存格式预览:")
        print(yaml_output)
        
    except Exception as e:
        print(f"配置保存测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_structure()
    config = test_config_loading()
    test_url_building(config)
    test_widget_creation()
    test_config_save()
    print("所有测试完成！")
