from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

driver_path = os.path.join("chromedriver", "chromedriver.exe")
wb = webdriver.Chrome(service=Service(driver_path))


login_url = "https://www.zhipin.com/web/user/?ka=header-login"
wb.get(login_url)
try:
    print(f"等待登陆...")
    WebDriverWait(wb, 60).until(
        EC.url_to_be(("https://www.zhipin.com/web/geek/job-recommend"))
    )
    print(f"登陆成功，自动跳转到主页。")
except Exception as e:
    print(f"页面跳转失败: {e}")
    
wb.get

pass