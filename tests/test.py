# -*- coding:utf-8 -*-
import json
import os

city_list = {}
# 读取json文件
json_file_path = os.path.join('china.json')
if not os.path.exists(json_file_path):
    print(f"文件 {json_file_path} 不存在")
else:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        try:
            china_list = json.loads(f.read())['zpData']
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            print("请检查文件内容是否为有效的 JSON 格式")
        else:
            for province in china_list['cityList']:
                province_name = province['name']
                for city in province['subLevelModelList']:
                    city_name = city['name']
                    print(province_name, city_name)
                    city_id = city['code']
                    city_list[f"{city_name}"] = city_id

# 写入新的json文件
output_file_path = os.path.join('city_list.json')
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(city_list, f, ensure_ascii=False, indent=4)