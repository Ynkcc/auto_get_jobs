# src/browser_manager.py
import asyncio
import logging
import random
import json
import os
from playwright.async_api import async_playwright, Response, Page, Error
from typing import List, Dict

from .common.event_manager import event_manager
from .common.file_utils import build_search_url

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, config, stop_flag):
        self.p_config = config.crawler.playwright
        self.accounts_config = config.accounts[0] if config.accounts else None
        self.job_search_config = config.job_search
        
        self.stop_flag = stop_flag
        self.playwright = None
        self.browser = None
        self.page = None
        self.save_task = None
        self.has_more_data_map = {}
        # 用于存储User-Agent，避免重复获取
        self.user_agent = None

    async def _handle_response(self, response: Response):
        """监听职位列表API响应"""
        if "wapi/zpgeek/search/joblist.json" in response.url:
            logger.debug(f"监听到职位列表API响应: {response.url}")
            try:
                data = await response.json()
                if data.get("code") == 0 and "zpData" in data:
                    zp_data = data["zpData"]
                    job_list = zp_data.get("jobList", [])
                    
                    current_url = self.page.url.split('?')[0]
                    self.has_more_data_map[current_url] = zp_data.get("hasMore", False)

                    if not job_list:
                        logger.warning("本次API响应中职位列表为空")
                        return
                    
                    await event_manager.publish("job_list_found", jobs=job_list)
                else:
                    logger.error(f"接口响应数据格式错误: {data}")
            except Exception as e:
                logger.error(f"处理职位列表响应时发生异常: {e}", exc_info=True)

    async def _initialize_browser(self):
        """初始化 Playwright 浏览器实例和页面对象。"""
        if self.page:
            return
        try:
            logger.info("正在初始化 Playwright 浏览器...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.p_config.headless)
            context = await self.browser.new_context()
            self.page = await context.new_page()
            logger.info("浏览器初始化成功。")
        except Error as e:
            logger.error(f"初始化浏览器失败: {e}", exc_info=True)
            self.stop_flag.set()
            raise

    async def login_and_setup(self) -> bool:
        """
        执行浏览器初始化、用户登录，并设置好后续爬取所需的监听器和定时任务。
        这是核心的流程控制函数。
        """
        if not self.accounts_config:
            logger.error("未配置任何账号信息，BrowserManager无法启动。")
            self.stop_flag.set()
            return False

        try:
            await self._initialize_browser()
            
            login_success = await self._login()
            if not login_success:
                logger.error("登录失败，将不会开始爬取任务。")
                self.stop_flag.set()
                return False

            # --- 修复后的核心逻辑 ---
            # 登录成功后, 在这里统一进行所有依赖登录状态的设置
            
            # 1. 首先获取并存储 User-Agent
            self.user_agent = await self.page.evaluate('() => navigator.userAgent')
            logger.info(f"成功获取并存储 User-Agent: {self.user_agent}")

            # 2. 然后，首次发布包含了正确User-Agent的会话数据
            await self._publish_session_data()

            # 3. 接着，启动需要会话数据的后台定时任务
            await self._start_autosave_timer()
            
            # 4. 最后，注册页面事件监听器
            self.page.on("response", self._handle_response)
            
            logger.info("登录和环境设置成功，准备就绪。")
            return True
            # --- 修复逻辑结束 ---

        except Exception as e:
            logger.error(f"登录和设置过程中发生严重错误: {e}", exc_info=True)
            self.stop_flag.set()
            return False

    async def start_crawling(self):
        """
        开始执行爬取任务，遍历搜索URL并滚动页面以加载数据。
        """
        if not self.page or self.page.is_closed():
            logger.error("无法开始爬取：浏览器页面未初始化或已关闭。")
            self.stop_flag.set()
            return

        try:
            url_list = build_search_url(self.job_search_config)
            logger.info(f"共生成 {len(url_list)} 个搜索URL")

            for i, url in enumerate(url_list):
                if self.stop_flag.is_set():
                    logger.info("接收到停止信号，停止爬取新页面。")
                    break
                
                logger.info(f"({i+1}/{len(url_list)}) 正在导航至: {url}")
                await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(5)

                current_url_key = self.page.url.split('?')[0]
                self.has_more_data_map[current_url_key] = True

                scroll_count = 0
                while self.has_more_data_map.get(current_url_key, False):
                    if self.stop_flag.is_set():
                        break
                    
                    scroll_count += 1
                    logger.info(f"正在为URL '{url}' 进行第 {scroll_count} 次滚动加载...")
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(random.uniform(3, 5))

                logger.info(f"URL '{url}' 已无更多数据，停止滚动。")

            logger.info("所有搜索URL已处理完毕。")

        except Exception as e:
            logger.error(f"爬取过程中发生严重错误: {e}", exc_info=True)
        finally:
            logger.info("爬取任务结束，设置停止标志以关闭整个程序。")
            self.stop_flag.set()

    async def _load_login_data(self) -> bool:
        """从文件加载登录数据（cookies）"""
        login_file = self.accounts_config.login_data_file if self.accounts_config else None
        if not login_file or not os.path.exists(login_file):
            logger.warning("登录数据文件不存在或未配置，将进行扫码登录")
            return False
        
        try:
            with open(login_file, "r", encoding="utf-8") as f:
                login_data = json.load(f)

            await self.page.context.clear_cookies()
            if login_data.get("cookies"):
                await self.page.context.add_cookies(login_data["cookies"])

            await self.page.goto("https://www.zhipin.com/web/user/?ka=header-login", wait_until='domcontentloaded')
            await self.page.wait_for_timeout(2000)
            
            if await self.page.locator('a[ka="header-username"]').count() > 0:
                logger.info("通过加载登录数据成功登录")
                return True
            else:
                logger.warning("加载的登录数据已失效，请重新扫码登录")
                return False
        except Exception as e:
            logger.error(f"加载登录数据失败: {e}", exc_info=True)
            return False

    async def _save_login_data(self):
        """保存当前登录数据（cookies）到文件"""
        login_file = self.accounts_config.login_data_file if self.accounts_config else None
        if not login_file:
            return False
        try:
            directory = os.path.dirname(login_file)
            if directory:
                os.makedirs(directory, exist_ok=True)

            cookies = await self.page.context.cookies()
            login_data = { "cookies": cookies }

            with open(login_file, "w", encoding="utf-8") as f:
                json.dump(login_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("登录数据已保存")
            return True
        except Exception as e:
            logger.error(f"保存登录数据失败: {e}", exc_info=True)
            return False
    
    async def _publish_session_data(self):
        """获取当前会话数据并发布事件以同步 ZhipinApi"""
        try:
            # 增加健壮性检查，确保User-Agent已设置
            if not self.user_agent:
                logger.warning("User-Agent 尚未设置，暂时无法发布会话数据。")
                return
            
            cookies = await self.page.context.cookies()
            headers = {'User-Agent': self.user_agent}
            await event_manager.publish("cookies_updated", cookies_data={"cookies": cookies, "headers": headers})
            logger.info("会话数据已发布，用于 ZhipinApi 同步")
        except Exception as e:
            logger.error(f"发布会话数据时出错: {e}", exc_info=True)

    async def _start_autosave_timer(self, interval=60):
        """启动定时保存登录数据并发布更新事件的任务"""
        logger.info(f"自动保存与会话更新任务已启动，间隔: {interval}秒")
        
        async def saver():
            while not self.stop_flag.is_set():
                await self._save_login_data()
                await self._publish_session_data()
                
                try:
                    # 使用asyncio.sleep，而不是time.sleep
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
        self.save_task = asyncio.create_task(saver())

    async def _stop_autosave_timer(self):
        """停止定时保存任务"""
        if self.save_task and not self.save_task.done():
            self.save_task.cancel()
            try:
                await self.save_task
            except asyncio.CancelledError:
                pass
            logger.info("自动保存任务已停止")

    async def _login(self) -> bool:
        """
        执行登录流程，此函数现在只负责登录，不处理任何后续设置。
        """
        if await self._load_login_data():
            # 成功后直接返回，不再发布事件
            return True
        
        logger.info("请在浏览器中扫码登录...")
        await self.page.goto("https://www.zhipin.com/web/user/?ka=header-login", wait_until='domcontentloaded')
        try:
            await self.page.locator('a[ka="header-username"]').wait_for(timeout=200000)
            logger.info("扫码登录成功")
            await self._save_login_data()
            # 成功后直接返回，不再发布事件
            return True
        except asyncio.TimeoutError:
            logger.error("登录超时（200秒），请重新运行程序", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"登录过程中发生未知错误: {e}", exc_info=True)
            return False

    async def close(self, **kwargs):
        """关闭浏览器和相关资源"""
        logger.info("正在关闭浏览器...")
        await self._stop_autosave_timer()
        try:
            if self.page and not self.page.is_closed():
                self.page.remove_listener("response", self._handle_response)
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"关闭浏览器时发生错误: {e}", exc_info=True)
        logger.info("浏览器已成功关闭")