from playwright.sync_api import sync_playwright

def open_boss_login():
    with sync_playwright() as p:
        # 启动浏览器（默认使用 Chromium）
        browser = p.chromium.launch(headless=False)  # headless=False 表示显示浏览器界面
        context = browser.new_context()
        
        try:
            # 创建新页面
            page = context.new_page()
            
            # 导航到目标页面
            page.goto('https://www.zhipin.com/web/user/?ka=header-login', timeout=60000)
            
            # 等待登录区域加载（可能需要调整选择器）
            #page.wait_for_selector('div.login-form', timeout=15000)
            
            # 截图演示（可选）
            #page.screenshot(path='boss_login_page.png')
            
            # 保持页面打开状态供观察
            input("按 Enter 键关闭浏览器...")
            
        except Exception as e:
            print(f"发生错误: {str(e)}")
        finally:
            # 关闭浏览器
            browser.close()

if __name__ == "__main__":
    open_boss_login()
