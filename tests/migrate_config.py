#!/usr/bin/env python3
# migrate_config.py - 配置文件迁移工具

import os
import yaml
import json
import shutil
from datetime import datetime

def load_search_params_mapping():
    """加载搜索参数映射"""
    try:
        config_path = os.path.join('config', 'search_params_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"搜索参数配置文件未找到: {config_path}")
        return {}

def migrate_filter_config(old_config, field_name, params_mapping):
    """迁移过滤配置"""
    if field_name not in old_config:
        return {"values": [0], "combine": True}
    
    old_field = old_config[field_name]
    
    # 如果已经是新格式，直接返回
    if isinstance(old_field, dict) and 'values' in old_field and 'combine' in old_field:
        # 检查values是否需要转换
        if isinstance(old_field['values'], list) and old_field['values']:
            # 尝试将字符串值转换为代码
            new_values = []
            field_mapping = params_mapping.get(field_name, {})
            
            for value in old_field['values']:
                if isinstance(value, str) and value in field_mapping:
                    new_values.append(field_mapping[value])
                elif isinstance(value, int):
                    new_values.append(value)
                elif value == '' or value is None:
                    continue  # 跳过空值
                else:
                    print(f"警告：无法转换值 '{value}' 在字段 '{field_name}' 中")
            
            return {
                "values": new_values if new_values else [0],
                "combine": old_field.get('combine', True)
            }
        else:
            return {"values": [0], "combine": old_field.get('combine', True)}
    
    # 如果是旧格式的列表，转换为新格式
    elif isinstance(old_field, list):
        new_values = []
        field_mapping = params_mapping.get(field_name, {})
        
        for value in old_field:
            if isinstance(value, str) and value in field_mapping:
                new_values.append(field_mapping[value])
            elif isinstance(value, int):
                new_values.append(value)
            elif value == '' or value is None:
                continue  # 跳过空值
            else:
                print(f"警告：无法转换值 '{value}' 在字段 '{field_name}' 中")
        
        return {
            "values": new_values if new_values else [0],
            "combine": True
        }
    
    # 默认返回
    return {"values": [0], "combine": True}

def migrate_config_file(input_file, output_file):
    """迁移配置文件"""
    print(f"开始迁移配置文件: {input_file} -> {output_file}")
    
    # 加载搜索参数映射
    params_mapping = load_search_params_mapping()
    
    # 读取原配置文件
    with open(input_file, 'r', encoding='utf-8') as f:
        old_config = yaml.safe_load(f)
    
    # 备份原文件
    backup_file = f"{input_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(input_file, backup_file)
    print(f"原配置文件已备份至: {backup_file}")
    
    # 迁移job_search配置
    if 'job_search' in old_config:
        job_search = old_config['job_search']
        
        # 迁移多选字段
        multi_select_fields = ['experience', 'degree', 'salary', 'scale', 'stage', 'jobType']
        for field in multi_select_fields:
            job_search[field] = migrate_filter_config(job_search, field, params_mapping)
        
        # 确保position和industry是列表
        if 'position' in job_search and isinstance(job_search['position'], dict):
            job_search['position'] = job_search['position'].get('values', [])
        
        if 'industry' in job_search and isinstance(job_search['industry'], dict):
            job_search['industry'] = job_search['industry'].get('values', [])
    
    # 保存新配置文件
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(old_config, f, allow_unicode=True, sort_keys=False, indent=2)
    
    print(f"配置文件迁移完成: {output_file}")

def main():
    """主函数"""
    config_file = 'config/config.yaml'
    
    if not os.path.exists(config_file):
        print(f"配置文件不存在: {config_file}")
        return
    
    # 迁移配置文件
    migrate_config_file(config_file, config_file)
    
    print("\n迁移完成！请重新运行应用程序。")

if __name__ == "__main__":
    main()
