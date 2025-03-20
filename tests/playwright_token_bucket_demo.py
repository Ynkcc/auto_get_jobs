import asyncio
from playwright.async_api import async_playwright
from pyrate_limiter import Duration, RequestRate, Limiter  # 使用 pyrate_limiter 库

# 定义全局速率限制（如 5 请求/秒）
rate = RequestRate(5, Duration.SECOND)
limiter = Limiter(rate)

async def throttle_request(route):
    # 等待令牌可用（异步非阻塞）
    await limiter.try_acquire("target_api")
    # 放行请求（继续原始请求）
    await route.continue_()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 拦截所有目标 URL 的请求
        await page.route("https://api.target.com/*", throttle_request)
        
        # 发起测试请求（实际场景中可能是页面自动触发的 AJAX）
        await page.goto("https://your-website.com")
        
        # 保持页面打开观察行为
        await asyncio.sleep(60)
        await browser.close()

asyncio.run(main())
