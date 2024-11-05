from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from aiconfig import ai_response, ai_hr
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

def active_hr(boss_url, my_job_name, my_job_salary):
    """
    获取活跃的HR,HR活跃开始分析工作
    """
    active_hr_jobs = []
    #获取工作列表
    jobs = get_job_info()
    #获取单个工作详情页
    for job in jobs:
        job_link = job['job_link']
        job_detail = boss_url + job_link
        wb.get(job_detail)
        WebDriverWait(wb, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-boss-info"))
        )
        #bs4解析页面hr活跃度
        html_content = wb.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        try:
            hr_active_time = soup.find('span', class_='boss-active-time').text.strip()
            if hr_active_time in ["本月活跃", "2月内活跃","3月内活跃", "4月内活跃", "5月内活跃", "半年前活跃"]:
                print(f"HR不活跃，跳过当前岗位。活跃程度为：{hr_active_time}")
                continue
            #HR在线率搞获取岗位名称开始对比
            job_name = job['job_name']
            job_salary = job['job_salary']
            if check_position_match(job_name, job_salary, my_job_name, my_job_salary):
                check_job_match(soup)
            
            
            
            active_hr_jobs.append(job)
            time.sleep(5)
        except:
            print(f"解析失败，跳过当前岗位。")
            time.sleep(5)
            continue
    print(f"当前有效岗位数量为：{len(active_hr_jobs)}")
    return active_hr_jobs


def check_position_match(job_name, job_salary, my_job_name, my_job_salary):
    """
    检索岗位是否匹配
    """
    url = "https://api.siliconflow.cn/v1/chat/completions"  # OpenAI API的实际端点
    key =   # 替换为您的实际API密钥
    model = "Vendor-A/Qwen/Qwen2.5-72B-Instruct"  # 使用的模型
    content=f'你是一个经验丰富的HR，你的任务是判断当前招聘岗位和薪资水平是否和我所期望的岗位匹配，如果匹配输出true，不匹配则输出false，除了true和false不要输出任何多余的内容，不要对基本信息讨论。以下是基本信息：当前招聘的岗位为“{job_name}”，招聘的岗位薪资为“{job_salary}k”，我所期望的岗位为“{my_job_name}”，最低薪资为“{my_job_salary}k”。'
    ai_res = ai_response(url, key ,model ,content)
    print(f"招聘岗位:==={job_name}===,期望岗位：==={my_job_name}===,AI判断结果：{ai_res}")
    if ai_res.lower() == "true":
        return True

def check_job_match(soup):
    """
    检测岗位内容是否匹配
    """
    user_requirements = get_user_requirements()
    job_requirements = soup.find('div', class_='job-sec-text').text.strip()
    url = "https://api.siliconflow.cn/v1/chat/completions"  # OpenAI API的实际端点
    key =   # 替换为您的实际API密钥
    model = "Vendor-A/Qwen/Qwen2.5-72B-Instruct"  # 使用的模型
    first_response = ai_hr(url, key, model, job_requirements, user_requirements)
    final_analysis = ai_hr(url, key, model, job_requirements, user_requirements, first_response, data_analysis=True)
    print(f"初步分析结果:{first_response}")
    print(f"最终分析结果:{final_analysis}")
    return

def get_user_requirements():
    """
    获取用户简历
    """
    file_path = os.path.join("user_requirements.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError("用户简历文件不存在，请先创建。")
    with open(file_path, "r", encoding="utf-8") as f:
        user_requirements = f.read().strip()
        # print(user_requirements)
    return user_requirements
    

if __name__ == "__main__":
    query = "运维"
    city = "杭州"
    degree = None
    # search(query, city,degree)
    my_job_name = "运维"
    my_job_salary = 5
    boss_url = "https://www.zhipin.com"
    search(query, city, degree = None)
    active_hr(boss_url, my_job_name, my_job_salary)
    wb.quit()