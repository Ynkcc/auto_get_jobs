import sys
import os
import json
# 将父目录添加到模块搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# 新增代码结束

from utils_database import DatabaseManager
import pandas as pd
# 1. 实例化数据库管理对象
db_manager = DatabaseManager('jobs.db')  # 确保路径正确

# 2. 转换CSV数据为字典列表
jobs_df = pd.read_csv('jobs.csv')
jobs_details_df = pd.read_csv('jobsDetails.csv')
jobs = jobs_df.to_dict('records')
jobs_details = jobs_details_df.to_dict('records')

for job in jobs:
    job["company_tags"]=eval(job["company_tags"])
import json
from ast import literal_eval

for jobs_detail in jobs_details:
    raw_data = jobs_detail["job_data"]
    try:
        # 先尝试标准JSON解析
        jobs_detail["job_data"] = json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            # 尝试解析Python字典格式（如使用单引号的情况）
            jobs_detail["job_data"] = literal_eval(raw_data)  # 比eval安全
        except:
            # 记录错误数据，保持原始值或设为None
            print(f"Failed to parse: {raw_data}")
            jobs_detail["job_data"] = None  # 或保持原始字符串

# 3. 调用保存方法（需注意异常处理）
db_manager.save_jobs_details(jobs, jobs_details)
print("数据保存成功")