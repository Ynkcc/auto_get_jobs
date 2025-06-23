# src/common/file_utils.py
import csv
import logging
from typing import List, Dict
import json
from urllib.parse import urlencode
import itertools
import os
import hashlib
import re

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)

def save_jobs_to_csv(jobs: List[Dict], filename: str = "jobs.csv"):
    """
    将职位列表保存到CSV文件。
    """
    if not jobs:
        return

    keys = jobs[0].keys()
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(jobs)
        logger.info(f"成功将 {len(jobs)} 个职位保存到 {filename}")
    except IOError as e:
        logger.error(f"保存CSV文件时出错: {e}", exc_info=True)


def export_to_xlsx(jobs_data: List[Dict], filename="filtered_jobs.xlsx"):
    """
    使用pandas将职位数据导出到xlsx文件。
    """
    if pd is None:
        logger.error("需要安装 'pandas' 和 'openpyxl' 库才能导出为xlsx文件。")
        logger.error("请运行: pip install pandas openpyxl")
        return

    if not jobs_data:
        logger.info("没有数据可以导出到Excel。")
        return

    try:
        df = pd.DataFrame(jobs_data)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"成功将 {len(jobs_data)} 条数据导出到 {filename}")
    except Exception as e:
        logger.error(f"导出到Excel文件时出错: {e}", exc_info=True)

def build_search_url(job_search) -> List[str]:
    """
    根据配置构造搜索URL。
    (从旧版 general.py 迁移而来)
    """
    # 假设 search_params_config.json 在 config/ 目录下
    config_path = os.path.join('config', 'search_params_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            params_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"搜索参数配置文件未找到: {config_path}")
        raise

    location_dicts = {}
    city_code_map = params_data["cityCode"]

    if job_search.areas:
        for city_name, districts in job_search.areas.items():
            city_entry = city_code_map.get(city_name, {})
            if not city_entry:
                logger.warning(f"未找到城市 [{city_name}] 的编码，已跳过")
                continue
            
            city_code = list(city_entry.keys())[0]
            valid_districts = [city_entry[city_code][d] for d in districts if d in city_entry[city_code]]
            if valid_districts:
                location_dicts.setdefault(city_code, []).extend(valid_districts)
    else:
        for city_name in job_search.city.values:
            city_entry = city_code_map.get(city_name)
            if not city_entry:
                logger.warning(f"未找到城市 [{city_name}] 的编码，已跳过")
                continue
            
            city_code = list(city_entry.keys())[0]
            if job_search.city.expand_to_district:
                location_dicts[city_code] = list(city_entry[city_code].values())
            else:
                location_dicts[city_code] = []

    if not location_dicts:
        raise ValueError("未找到有效的城市/区域配置")

    base_url = "https://www.zhipin.com/web/geek/job"

    def process_filter(filter_config, param_map: dict) -> List[str]:
        codes = [str(param_map.get(v)) for v in filter_config.values]
        return [','.join(c for c in codes if c)] if filter_config.combine and codes else [c for c in codes if c]

    params_config = {
        'degree': process_filter(job_search.degree, params_data.get("degree", {})),
        'experience': process_filter(job_search.experience, params_data.get("experience", {})),
        'scale': process_filter(job_search.scale, params_data.get("scale", {})),
        'stage': process_filter(job_search.stage, params_data.get("stage", {})),
        'salary': [str(params_data.get("salary", {}).get(v)) for v in job_search.salary],
        'query': job_search.query
    }
    params_config = {k: v for k, v in params_config.items() if any(v)}

    base_params_list = []
    for city_code, districts in location_dicts.items():
        if not districts:
            base_params_list.append({'city': city_code})
            continue
        for district_code in districts:
            base_params_list.append({'city': city_code, 'businessDistrict': district_code})

    url_list = []
    param_keys = list(params_config.keys())
    param_combinations = list(itertools.product(*params_config.values()))

    for base_param in base_params_list:
        for combination in param_combinations:
            merged_params = base_param.copy()
            merged_params.update(zip(param_keys, combination))
            param_str = urlencode(merged_params)
            url_list.append(f"{base_url}?{param_str}")

    return url_list if url_list else [f"{base_url}?{urlencode(p)}" for p in base_params_list]


def calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值。
    (从旧版 general.py 迁移而来)
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def filter_jobs_by_salary(jobs: List[Dict], min_expected_salary: float, max_expected_salary: float) -> List[Dict]:
    """
    根据期望薪资范围过滤岗位。
    (从旧版 general.py 迁移而来)
    """
    jobs_matching_salary = []

    for job in jobs:
        # 在重构后的架构中，job 是一个包含 jobCard 的字典
        job_card = job.get('jobCard', {})
        job_name = job_card.get('jobName', '未知职位')
        job_salary = job_card.get('salaryDesc', '')
        if not job_salary:
            continue

        try:
            salary_str = re.sub(r'·\d+薪', '', job_salary).lower()
            
            min_monthly = 0
            max_monthly = 0

            if 'k' in salary_str:
                parts = salary_str.replace('k', '').split('-')
                min_monthly = float(parts[0])
                max_monthly = float(parts[-1])
            elif '元/天' in salary_str:
                parts = salary_str.replace('元/天', '').split('-')
                min_monthly = float(parts[0]) * 22 / 1000
                max_monthly = float(parts[-1]) * 22 / 1000
            # 可根据需要添加更多薪资格式的处理

            if min_expected_salary <= min_monthly and max_monthly <= max_expected_salary:
                jobs_matching_salary.append(job)
        except (ValueError, IndexError):
            logger.warning(f"无法解析薪资: {job_salary} (职位: {job_name})")
            continue

    return jobs_matching_salary