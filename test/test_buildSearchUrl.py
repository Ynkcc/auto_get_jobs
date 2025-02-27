import sys
import os
# 将父目录添加到模块搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from utils import *
import yaml

config=load_config("config.yaml")
urls=[]
for url in buildSearchUrl(config["job_search"]):
    urls.append(url)
    print(url)


print(len(urls))

urls = list(set(urls))
print(len(urls))


