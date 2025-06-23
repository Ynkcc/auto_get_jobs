#!/usr/bin/env python3
"""
测试事件流程的简单脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config_manager import ConfigManager
from src.utils.event_manager import event_manager
from src.utils.job_filter import JobFilter
from src.utils.job_analyzer import JobAnalyzer
from src.utils.db_utils import DatabaseManager

async def test_event_flow():
    """测试完整的事件流程"""
    print("🧪 开始测试事件流程...")
    
    # 1. 加载配置
    ConfigManager.load_config("config/config.yaml")
    config = ConfigManager.get_config()
    
    # 2. 初始化组件
    job_filter = JobFilter(config)
    job_analyzer = JobAnalyzer(config)
    db_manager = DatabaseManager(config.database.filename)
    
    # 3. 注册事件订阅
    event_manager.subscribe("job_list_found", job_filter.pre_filter_jobs)
    event_manager.subscribe("job_list_found", db_manager.save_initial_jobs)
    event_manager.subscribe("jobs_pre_filtered", job_analyzer.process_job_list)
    event_manager.subscribe("job_analysis_complete", db_manager.update_job_analysis)
    
    # 4. 模拟职位数据（匹配JobProcessor期望的格式）
    mock_jobs = [
        {
            "encryptJobId": "test_job_001",
            "job_name": "Python开发工程师",
            "company_name": "测试科技公司", 
            "job_salary": "15-25K",
            "city_name": "北京",
            "job_description": "负责Python后端开发，熟悉Django/Flask框架",
            "experience_name": "1-3年",
            "degree_name": "本科",
            "active_time_desc": "3日内活跃"
        },
        {
            "encryptJobId": "test_job_002",  
            "job_name": "运维工程师",
            "company_name": "云端科技",
            "job_salary": "12-18K",
            "city_name": "上海", 
            "job_description": "负责Linux系统运维，熟悉Docker、K8s",
            "experience_name": "1-3年",
            "degree_name": "专科",
            "active_time_desc": "今日活跃"
        }
    ]
    
    # 5. 发布职位发现事件
    print("📋 发布职位列表发现事件...")
    await event_manager.publish("job_list_found", jobs=mock_jobs)
    
    # 给一些时间让事件处理完成
    await asyncio.sleep(2)
    
    print("✅ 事件流程测试完成！")
    print("💡 检查日志以查看详细的事件处理过程")

if __name__ == "__main__":
    asyncio.run(test_event_flow())
