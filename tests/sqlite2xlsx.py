import sqlite3
import pandas as pd

# 连接数据库
conn = sqlite3.connect('data/jobs.db')

# 读取数据
df = pd.read_sql_query("SELECT * FROM job_details", conn)

# 导出Excel
df.to_excel("output.xlsx", index=False, engine='openpyxl')

# 关闭连接
conn.close()