import re
import pandas as pd
def check_position_match(query, my_job_salary):
    """
    检查岗位是否匹配薪资范围
    query: 岗位名称
    my_job_salary: 我的期望薪资（单位：K）
    """
    jobs_df = pd.read_csv('jobs.csv')  # 读取 CSV 文件
    jobs = jobs_df.to_dict('records')
    print(f"根据当前数据，城市中总共有 {len(jobs)} 个岗位可供选择。")
    position_matches = []

    for job in jobs:
        job_name = job['job_name']
        job_salary = job['job_salary']

        # 使用正则表达式去除类似 "·13薪" 的后缀
        job_salary = re.sub(r'·\d+薪', '', job_salary)

        # 解析薪资范围
        if '元/天' in job_salary:
            # 处理日薪情况，按每月22天计算月薪
            daily_salary = job_salary.replace('元/天', '')
            daily_salary_range = daily_salary.split('-')
            min_daily_salary = int(daily_salary_range[0])
            max_daily_salary = int(daily_salary_range[1]) if len(daily_salary_range) > 1 else min_daily_salary
            min_monthly_salary = min_daily_salary * 22 / 1000  # 转换为K
            max_monthly_salary = max_daily_salary * 22 / 1000  # 转换为K
        elif "k" in job_salary or "K" in job_salary:
            # 处理月薪情况
            salary_range = job_salary.replace('K', '').replace('k', '').split('-')
            min_monthly_salary = float(salary_range[0])
            max_monthly_salary = float(salary_range[1]) if len(salary_range) > 1 else min_monthly_salary
        else:
            #格式不对，直接放弃
            print(f"薪资格式错误：招聘岗位: {job_name} | {job_salary}")
            continue
        # 判断薪资是否满足条件
        if min_monthly_salary >= my_job_salary:
            position_matches.append(job)
            print(f"招聘岗位: {job_name}  |  期望岗位: {query}  |  薪资范围: {min_monthly_salary}-{max_monthly_salary}K  |  匹配结果: 匹配")
        else:
            print(f"招聘岗位: {job_name}  |  期望岗位: {query}  |  薪资范围: {min_monthly_salary}-{max_monthly_salary}K  |  匹配结果: 不匹配")

    print(f"根据当前数据，系统筛选出符合要求的岗位总数为: {len(position_matches)} 个。")
    return position_matches


check_position_match(None,6)