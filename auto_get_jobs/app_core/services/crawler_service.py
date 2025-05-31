# app_core/services/crawler_service.py
import logging
import time
import asyncio
from typing import Optional, List, Dict, Any
import threading # 确保导入

from playwright.async_api import async_playwright, Page, Browser, Playwright

from .base_service import BaseService
from app_core.models.job import JobStatus # 确保 JobStatus 被导入
from app_core.utils.config_manager import ConfigManager # 用于加载城市代码和搜索参数
# from app_core.utils.general_utils import build_search_url, extract_job_id_from_url, throttle_request # 通用工具
# from app_core.app_controller import AppController # 仅用于类型提示

logger = logging.getLogger(__name__)

class CrawlerService(BaseService):
    def __init__(self, config: dict, db_manager, ui_updater, stop_event: threading.Event, app_controller = None): # app_controller: 'AppController'
        super().__init__(config, db_manager, ui_updater, stop_event, app_controller)
        
        self.playwright_config = self.config.get('playwright', {})
        self.search_url_config = self.config.get('search_url', {})
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        
        self._last_request_time_ref = [0] # 用于请求节流
        self._session_manager = None # SessionManager 实例，在 _initialize_playwright 中创建

        # 从AppController获取或创建内部事件循环来运行Playwright的异步操作
        # 如果服务有自己的事件循环需求，或者AppController的事件循环可以共享
        # 这里假设我们将使用AppController的事件循环 (通过self._submit_app_controller_task)
        # 或者，CrawlerService可以创建并管理自己的asyncio事件循环在其_run线程中

    async def _initialize_playwright(self):
        """(异步) 初始化 Playwright 驱动、浏览器和页面。"""
        if self._page and not self._page.is_closed():
            logger.info("Playwright 页面已初始化。")
            return True

        self._log_to_ui("正在初始化浏览器驱动...", "info")
        logger.info("CrawlerService: 正在初始化 Playwright...")
        try:
            self._playwright = await async_playwright().start()
            browser_type = getattr(self._playwright, self.playwright_config.get("browser", "chromium"))
            
            launch_options = {"headless": self.playwright_config.get("headless", True)}
            if self.playwright_config.get("user_data_dir"):
                launch_options["user_data_dir"] = self.playwright_config.get("user_data_dir")
            if self.playwright_config.get("proxy", {}).get("server"):
                launch_options["proxy"] = self.playwright_config.get("proxy")
            
            self._browser = await browser_type.launch(**launch_options)
            
            # SessionManager 的导入路径需要确认，假设它在 app_core.utils.session_manager
            # from app_core.utils.session_manager import SessionManager # 移到文件顶部
            # self._session_manager = SessionManager(self._browser, self.playwright_config.get("user_agent"))
            
            # 暂时直接创建页面，SessionManager的逻辑可以后续集成
            context = await self._browser.new_context(
                user_agent=self.playwright_config.get("user_agent"),
                # ... 其他 context 选项 ...
            )
            # 加载cookies (如果配置了)
            cookie_file = self.playwright_config.get("cookie_file")
            if cookie_file:
                try:
                    with open(cookie_file, 'r') as f:
                        cookies = json.load(f) # 需要 import json
                    await context.add_cookies(cookies)
                    logger.info(f"已从 {cookie_file} 加载cookies。")
                except Exception as e:
                    logger.warning(f"加载cookies文件 {cookie_file} 失败: {e}")

            self._page = await context.new_page()
            logger.info("CrawlerService: Playwright 初始化完成，页面已创建。")
            self._log_to_ui("浏览器驱动初始化完成。", "info")
            return True
        except Exception as e:
            logger.error(f"CrawlerService: Playwright 初始化失败: {e}", exc_info=True)
            self._log_to_ui(f"浏览器驱动初始化失败: {e}", "error")
            await self._cleanup_playwright()
            return False

    async def _login_if_needed(self):
        """(异步) 如果需要，执行登录操作。"""
        if not self._page or self._page.is_closed():
            logger.error("CrawlerService: 页面未初始化，无法执行登录。")
            return False

        login_url = self.search_url_config.get("login_url")
        success_locator_str = self.search_url_config.get("login_success_flag_locator")
        login_timeout_sec = self.search_url_config.get("login_timeout", 60)

        if not login_url or not success_locator_str:
            logger.info("CrawlerService: 未配置登录URL或成功标志，跳过登录检查。")
            return True # 假设不需要登录

        self._log_to_ui("正在检查登录状态...", "info")
        logger.info(f"CrawlerService: 正在导航到登录/检查页面: {login_url}")
        try:
            await self._page.goto(login_url, wait_until="networkidle", timeout=self.playwright_config.get("page_load_timeout", 30) * 1000)
            
            success_locator = self._page.locator(success_locator_str)
            if await success_locator.count() > 0:
                logger.info("CrawlerService: 已检测到登录状态。")
                self._log_to_ui("已登录。", "info")
                # 保存cookies
                cookie_file = self.playwright_config.get("cookie_file")
                if cookie_file:
                    cookies = await self._page.context.cookies()
                    with open(cookie_file, 'w') as f:
                        json.dump(cookies, f) #需要 import json
                    logger.info(f"Cookies已保存到 {cookie_file}")
                return True

            self._log_to_ui(f"未登录。请在浏览器中手动登录，超时时间: {login_timeout_sec}秒...", "warning")
            logger.warning(f"CrawlerService: 未检测到登录成功标志 {success_locator_str}。请手动登录...")
            
            await success_locator.wait_for(timeout=login_timeout_sec * 1000)
            logger.info("CrawlerService: 手动登录成功（检测到成功标志）。")
            self._log_to_ui("手动登录成功。", "info")
            # 保存cookies
            cookie_file = self.playwright_config.get("cookie_file")
            if cookie_file:
                cookies = await self._page.context.cookies()
                with open(cookie_file, 'w') as f: # 需要 import json
                    json.dump(cookies, f)
                logger.info(f"Cookies已保存到 {cookie_file}")
            return True
        except Exception as e:
            logger.error(f"CrawlerService: 登录检查或手动登录等待失败: {e}", exc_info=True)
            self._log_to_ui(f"登录失败: {e}", "error")
            return False

    async def _scrape_job_list_page(self, url: str, city_name: str, search_param_name: str) -> List[Dict[str, Any]]:
        """(异步) 抓取单个职位列表页面的所有职位信息。"""
        if not self._page or self._page.is_closed():
            logger.error("CrawlerService: 页面未初始化，无法抓取。")
            return []
        
        jobs_on_page = []
        try:
            self._log_to_ui(f"正在访问: {url}", "debug")
            logger.info(f"CrawlerService: 正在导航到职位列表页: {url}")
            await self._page.goto(url, wait_until="networkidle", timeout=self.playwright_config.get("page_load_timeout", 30) * 1000)
            
            # 使用配置中的定位器来查找职位列表项
            # TODO: 这里的定位器和提取逻辑需要根据目标网站的HTML结构在配置文件中详细定义
            # 例如: self.config.get('selectors', {}).get('job_item_selector', 'div.job-item')
            job_item_selector = self.config.get('job_list_selectors', {}).get('job_item', 'YOUR_JOB_ITEM_CSS_SELECTOR')
            
            job_elements = await self._page.locator(job_item_selector).all()
            self._log_to_ui(f"在页面 {url} 上找到 {len(job_elements)} 个疑似职位条目。", "info")
            
            job_id_patterns = self.config.get('job_id_extract_patterns', []) # 从配置获取提取ID的正则

            for el_index, job_el in enumerate(job_elements):
                if self.stop_event.is_set(): break
                try:
                    # --- TODO: 根据实际页面结构提取以下信息 ---
                    # 使用 self.config.get('job_list_selectors', {}) 中的具体选择器
                    title_selector = self.config.get('job_list_selectors',{}).get('title', 'a.job-title')
                    url_selector = self.config.get('job_list_selectors',{}).get('url', 'a.job-title') # URL通常在标题链接上
                    company_selector = self.config.get('job_list_selectors',{}).get('company', '.company-name')
                    location_selector = self.config.get('job_list_selectors',{}).get('location', '.job-location')
                    salary_selector = self.config.get('job_list_selectors',{}).get('salary', '.job-salary')
                    # ... 其他字段的selector ...
                    
                    job_title = await job_el.locator(title_selector).inner_text()
                    job_url_rel = await job_el.locator(url_selector).get_attribute('href')
                    job_url = self._page.urljoin(job_url_rel) if job_url_rel else None # 转换为绝对URL

                    company_name = await job_el.locator(company_selector).inner_text()
                    location = await job_el.locator(location_selector).inner_text()
                    salary = await job_el.locator(salary_selector).inner_text()
                    
                    job_id_from_site = extract_job_id_from_url(job_url, job_id_patterns)
                    if not job_id_from_site:
                        # 如果无法从URL提取，尝试从元素属性或其他地方提取
                        # job_id_from_site = await job_el.get_attribute('data-job-id')
                        logger.warning(f"未能从URL {job_url} 提取职位ID，请检查 job_id_extract_patterns 配置。")
                        # 使用URL的MD5作为备用ID (不理想，但确保唯一性)
                        job_id_from_site = hashlib.md5(job_url.encode()).hexdigest()[:16] #需要 import hashlib

                    job_data = {
                        "job_id": job_id_from_site,
                        "job_title": job_title.strip() if job_title else None,
                        "company_name": company_name.strip() if company_name else None,
                        "location": location.strip() if location else None,
                        "salary_range": salary.strip() if salary else None,
                        "source_url": job_url,
                        "source_platform": self.config.get("platform_name", "UnknownPlatform"), # 从配置定义平台名
                        # "job_description": "", # 详情页获取
                        "status": JobStatus.NEW, # 初始状态
                        "search_param_name": search_param_name,
                        "search_city_name": city_name,
                    }
                    jobs_on_page.append(job_data)
                    self._log_to_ui(f"提取到职位: {job_title}", "debug")
                except Exception as e_item:
                    logger.error(f"提取第 {el_index + 1} 个职位条目时出错: {e_item}", exc_info=False) #避免过多日志
                    self._log_to_ui(f"提取单个职位条目时出错: {e_item}", "warning")
            
        except Exception as e:
            logger.error(f"CrawlerService: 抓取职位列表页 {url} 失败: {e}", exc_info=True)
            self._log_to_ui(f"抓取页面 {url} 失败: {e}", "error")
        
        return jobs_on_page

    async def _process_job_url_list(self, urls_to_process: List[Dict[str, str]]):
        """(异步) 遍历并处理所有待抓取的职位列表URL。"""
        if not await self._initialize_playwright() or not await self._login_if_needed():
            self._log_to_ui("无法初始化浏览器或登录，爬虫任务中止。", "error")
            return

        total_urls = len(urls_to_process)
        processed_count = 0

        for i, url_info in enumerate(urls_to_process):
            if self.stop_event.is_set():
                self._log_to_ui("爬虫服务接收到停止信号，正在中断URL处理...", "info")
                break
            
            current_url = url_info["url"]
            city = url_info.get("city", "N/A")
            search_name = url_info.get("search_param_name", "N/A")
            
            self._log_to_ui(f"开始处理URL {i+1}/{total_urls} ({city}): {current_url}", "info")
            
            # 请求节流
            min_interval = self.playwright_config.get("navigation_delay", 2.0) # 从配置获取延迟
            throttle_request(self._last_request_time_ref, min_interval)

            extracted_jobs = await self._scrape_job_list_page(current_url, city, search_name)
            
            if extracted_jobs:
                self._log_to_ui(f"从 {current_url} 提取到 {len(extracted_jobs)} 个职位，正在存入数据库...", "info")
                for job_data in extracted_jobs:
                    if self.stop_event.is_set(): break
                    try:
                        # 检查职位是否已存在，如果存在则不添加或选择更新
                        # db_manager.add_job 方法内部应该有这种检查逻辑
                        self.db_manager.add_job(job_data)
                    except Exception as e_db:
                        logger.error(f"保存职位 {job_data.get('job_title')} 到数据库时出错: {e_db}", exc_info=True)
                        self._log_to_ui(f"保存职位 {job_data.get('job_title')} 失败: {e_db}", "error")
            
            processed_count += 1
            # TODO: 实现翻页逻辑 (如果需要)
            # 检查是否有下一页，如果有，则构建下一页URL并添加到urls_to_process或递归调用
            # has_next_page_selector = self.config.get('job_list_selectors', {}).get('next_page_button_enabled')
            # if has_next_page_selector and await self._page.locator(has_next_page_selector).count() > 0:
            #    ...

        self._log_to_ui(f"职位列表URL处理完成。共处理 {processed_count} 个基础URL。", "info")


    async def _cleanup_playwright(self):
        """(异步) 清理 Playwright 资源。"""
        logger.info("CrawlerService: 正在清理 Playwright 资源...")
        if self._page and not self._page.is_closed():
            try: await self._page.close()
            except Exception as e: logger.warning(f"关闭页面时出错: {e}")
        if self._browser and self._browser.is_connected():
            try: await self._browser.close()
            except Exception as e: logger.warning(f"关闭浏览器时出错: {e}")
        if self._playwright: # Playwright 实例本身不需要异步关闭
            try: await self._playwright.stop() # 异步停止
            except Exception as e: logger.warning(f"停止Playwright时出错: {e}")
        self._page, self._browser, self._playwright = None, None, None
        logger.info("CrawlerService: Playwright 资源已清理。")


    def _build_target_urls(self) -> List[Dict[str,str]]:
        """构建所有需要抓取的URL列表。"""
        urls_to_process = []
        search_params_list = ConfigManager.load_search_params_from_json(
            self.search_url_config.get("search_params_path", "config/search_params_config.json")
        )
        if not search_params_list:
            self._log_to_ui("错误: 未找到有效的搜索参数配置。", "error")
            return []

        # TODO: GUI应允许用户选择一个或多个搜索参数配置来执行
        # 目前简单处理：遍历所有配置的搜索参数
        for search_param_item in search_params_list:
            if self.stop_event.is_set(): break
            param_name = search_param_item.get('name', '未命名搜索')
            self._log_to_ui(f"正在为搜索配置 '{param_name}' 构建URL...", "info")

            if self.search_url_config.get("mode") == "city":
                city_codes_path = self.search_url_config.get("city_codes_path", "data/city_codes.json")
                city_codes = ConfigManager.load_city_codes(city_codes_path)
                if not city_codes:
                    self._log_to_ui(f"警告: 未能加载城市代码文件 {city_codes_path}", "warning")
                    continue
                for city_name, city_code in city_codes.items():
                    if self.stop_event.is_set(): break
                    url = build_search_url(search_param_item, self.search_url_config, city_code, city_name)
                    urls_to_process.append({"url": url, "city": city_name, "search_param_name": param_name})
            
            elif self.search_url_config.get("mode") == "custom":
                custom_jobs_config = self.search_url_config.get("custom_jobs", [])
                for custom_job_entry in custom_jobs_config:
                    if self.stop_event.is_set(): break
                    # custom_job_entry 可能包含 "url_template", "cityName", "cityCode"
                    url = build_search_url(
                        search_param_item, # 传递搜索参数（如关键词）给模板
                        self.search_url_config,
                        city_code=custom_job_entry.get("cityCode"),
                        city_name=custom_job_entry.get("cityName"),
                        custom_url_template=custom_job_entry.get("url_template") # 使用url_template字段
                    )
                    urls_to_process.append({
                        "url": url,
                        "city": custom_job_entry.get("cityName", "N/A"),
                        "search_param_name": param_name + "_" + custom_job_entry.get("name", "custom")
                    })
            else:
                # 单一URL模式或直接使用base_url (如果配置了)
                url = build_search_url(search_param_item, self.search_url_config)
                urls_to_process.append({"url": url, "city": "N/A", "search_param_name": param_name})

        self._log_to_ui(f"共构建 {len(urls_to_process)} 个目标URL进行抓取。", "info")
        return urls_to_process

    def _run(self):
        """爬虫服务的主要运行逻辑。"""
        self._log_to_ui("爬虫服务核心逻辑开始运行...", "info")
        
        # 这个方法在自己的线程中运行，但Playwright是异步的。
        # 我们需要一个事件循环来运行Playwright的异步代码。
        # 方案1: 在这个线程中创建并运行一个新的事件循环。
        # 方案2: 使用AppController提供的共享事件循环 (通过 self._submit_app_controller_task)。
        
        # 采用方案1: 在此线程中管理自己的事件循环
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.stop_event.is_set():
                self._log_to_ui("启动时检测到停止信号，爬虫服务不执行。", "info")
                return

            # 1. 构建目标URL列表 (同步操作)
            target_urls = self._build_target_urls()
            if not target_urls:
                self._log_to_ui("没有需要处理的URL，爬虫服务退出。", "info")
                return

            # 2. 运行异步的URL处理流程
            loop.run_until_complete(self._process_job_url_list(target_urls))

        except Exception as e:
            logger.error(f"CrawlerService _run 方法发生未知错误: {e}", exc_info=True)
            self._log_to_ui(f"爬虫服务遇到严重错误并终止: {e}", "error")
        finally:
            if loop: # 确保在finally中清理异步资源和循环
                logger.info("CrawlerService 开始清理异步资源...")
                if self._playwright: # 确保清理playwright
                    loop.run_until_complete(self._cleanup_playwright())
                
                # 关闭事件循环
                loop.close() # asyncio.new_event_loop() 创建的循环需要显式关闭
                logger.info("CrawlerService 的内部事件循环已关闭。")
            
            self._log_to_ui("爬虫服务核心逻辑已结束。", "info")
            # _is_running 会在 BaseService._service_wrapper 的 finally 中被更新
