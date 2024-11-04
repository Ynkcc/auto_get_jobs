from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from aiconfig import ai_response
import os
import time
import json

driver_path = os.path.join("chromedriver", "chromedriver.exe")
wb = webdriver.Chrome(service=Service(driver_path))

def login():
    """
    登录BOSS直聘
    """
    #登录URl
    login_url = "https://www.zhipin.com/web/user/?ka=header-login"
    wb.get(login_url)
    #等待用户登录登录成功跳转主页
    try:
        print(f"等待登陆...")
        WebDriverWait(wb, 60).until(
            EC.url_to_be(("https://www.zhipin.com/web/geek/job-recommend"))
        )
        print(f"登陆成功，自动跳转到主页。")
    except Exception as e:
        print(f"页面跳转失败: {e}")
    return
def search(query, city, degree = None):
    """
    构造搜索URL
    :param query: 职位
    :param city: 城市
    """
    
    cityid = get_cityid(city)
    serch_url = f"https://www.zhipin.com/web/geek/job?query={query}&city={cityid}"
    if degree:
        serch_url += f"&degree={degree}"
    wb.get(serch_url)
    time.sleep(3)
    try:
        print(f"等待页面加载完成...")
        WebDriverWait(wb, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-job-result"))
        )
        print(f"页面加载完成，开始筛选岗位。")
        
    except Exception as e:
        print(f"页面加载失败: {e}")
    return

def get_cityid(city):
    """
    获取城市的ID
    """
    cityid_dict = json.load(open("city_list.json", "r", encoding="utf-8"))
    cityid = cityid_dict[city]
    
    return cityid

def get_job_info():
    """
    获取岗位信息
    """
    jobs = []
    while True:
        html_content = wb.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        WebDriverWait(wb, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-card-wrapper"))
        )
        time.sleep(1)
        #超找鄋的岗位信息块
        job_cards = soup.find_all('li', class_='job-card-wrapper')

        # print(job_cards)
        for job_card in job_cards:
            #岗位名称
            job_name = job_card.find('span', class_="job-name").text.strip()
            # print(job_name)
            #薪资
            job_salary = job_card.find('span', class_="salary").text.strip()
            #岗位链接
            job_link = job_card.find('a', class_ = 'job-card-left')['href']
            
            jobs.append({
                'job_name': job_name,
                'job_salary': job_salary,
                'job_link': job_link
            })
            
        #下一页按钮的位置
        next_page_button = wb.find_element(By.CLASS_NAME, "ui-icon-arrow-right")
        print(next_page_button.find_element(By.XPATH, "..").get_attribute("class"))
        if "disabled" in next_page_button.find_element(By.XPATH, "..").get_attribute("class"):
            print("没有下一页了，退出循环。")
            break
        next_page_button.click()     
    return jobs

def chicke_job(my_job_name, my_job_salary):
    """
    检索岗位是否匹配
    """
    useful_jobs = []
    jobs = get_job_info()
    for job in jobs:
        job_name = job['job_name']
        job_salary = job['job_salary']
        
        url='https://api.siliconflow.cn/v1/chat/completions'
        key=''
        model='Vendor-A/Qwen/Qwen2.5-72B-Instruct'
        content=f'你是一个经验丰富的HR，你的任务是判断当前招聘岗位和薪资水平是否和我所期望的岗位匹配，如果匹配输出true，不匹配则输出false，除了true和false不要输出任何多余的内容，不要对基本信息讨论。以下是基本信息：当前招聘的岗位为“{job_name}”，招聘的岗位薪资为“{job_salary}k”，我所期望的岗位为“{my_job_name}”，最低薪资为“{my_job_salary}k”。'
        ai_res = ai_response(url, key ,model ,content)
        print(f"招聘岗位:==={job_name}===,期望岗位：==={my_job_name}===,AI判断结果：{ai_res}")
        if ai_res.lower() == "true":
            useful_jobs.append(job)
    return useful_jobs

def hr_activity():
    """
    检测hr活跃度
    """
    html_content = wb.page_source
    suop = BeautifulSoup(html_content, "html.parser")
    hr_active_time = suop.find('span', class_='boss-active-time')
    if hr_active_time in ["本月活跃", "2月内活跃","3月内活跃", "4月内活跃", "5月内活跃", "半年活跃"]:
        return False
    else:
        job_sec = suop.find('div', class_='job-sec-text').text.strip()
        url='https://api.siliconflow.cn/v1/chat/completions'
        key=''
        model='Vendor-A/Qwen/Qwen2.5-72B-Instruct'
        content=''
        return True
    

def view_job_details():
    url = "https://www.zhipin.com"
    useful_jobs = chicke_job(my_job_name, my_job_salary)
    for job in useful_jobs:
        job_link = job['job_link']
        wb.get(f'https://www.zhipin.com{job_link}')
        time.sleep(60)




if __name__ == "__main__":
    query = "运维"
    city = "杭州"
    degree = None
    # search(query, city,degree)
    my_job_name = "运维"
    my_job_salary = 5
    search(query, city, degree = None)
    view_job_details()
    wb.quit()