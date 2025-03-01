from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import initDriver, saveLoginData, loadLoginData, startCookieSaver, buildSearchUrl, getPageJobsInfo, filterJobsBySalary, nextPage
from job_processor import JobProcessor
from multiprocessing import Process, Queue, Event
import time

def login(driver):
    loginUrl = "https://www.zhipin.com/web/user/?ka=header-login"
    driver.get(loginUrl)

    print("等待用户登录...")
    if loadLoginData(driver):
        driver.get(loginUrl)

    WebDriverWait(driver, timeout=600).until(
        EC.presence_of_element_located((By.XPATH, '//a[@ka="header-username"]'))
    )

    saveLoginData(driver)
    startCookieSaver(driver)
    print("登录成功")

def mainLoop(driver, extraData):
    commQueue = Queue()
    doneEvent = Event()
    processor = JobProcessor(commQueue, doneEvent)
    
    process = Process(target=processor.startProcessing)
    process.start()

    try:
        targetUrl = buildSearchUrl(extraData["query"], extraData["city"])
        driver.get(targetUrl)
        
        while True:
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-card-wrapper"))
            )
            
            jobs = getPageJobsInfo(driver)
            validJobs = filterJobsBySalary(jobs, extraData["expectedSalary"])
            
            if validJobs:
                cookies = {c['name']: c['value'] for c in driver.get_cookies()}
                headers = {'User-Agent': driver.execute_script("return navigator.userAgent;")}
                
                commQueue.put({
                    "jobs": validJobs,
                    "cookies": cookies,
                    "headers": headers
                })
                doneEvent.clear()
                
                while not doneEvent.wait(timeout=60):
                    print("等待批次处理完成...")
                    time.sleep(5)
                    
            time.sleep(3)
            if not nextPage(driver):
                break
                
    finally:
        commQueue.put(None)
        process.join(timeout=30)

def main():
    driver = initDriver()
    login(driver)
    
    extraData = {
        "query": "运维",
        "city": "海口",
        "expectedSalary": 6
    }

    mainLoop(driver, extraData)

if __name__ == "__main__":
    main()
