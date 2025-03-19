import sys
import os
# 将父目录添加到模块搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from src.utils.general import build_search_url

from src.utils.config_manager import ConfigManager
import yaml

ConfigManager.load_config("config/config.yaml")
config = ConfigManager.get_config()
urls = build_search_url(config.job_search)

print(len(urls))

urls = list(set(urls))
print(len(urls))


