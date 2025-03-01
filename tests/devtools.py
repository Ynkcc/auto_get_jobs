from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 配置 Chrome 启动选项
chrome_options = Options()
chrome_options.add_experimental_option("w3c", False)  # 禁用 W3C 模式以启用 DevTools Protocol

# 启动浏览器
driver = webdriver.Chrome(options=chrome_options)

# 启用 DevTools 协议并捕获网络请求
dev_tools = driver.execute_cdp_cmd("Network.enable", {})

def log_response(response):
    if 'xhr' in response.get('type', ''):
        print(response)

# 设置监听响应
driver.request_interceptor = log_response

# 打开页面
driver.get("http://baidu.com")

# 等待一些时间以便捕获请求
import time
time.sleep(5)

driver.quit()
