import logging
logger = logging.getLogger(__name__)
import traceback
import asyncio
from utils.general import *
from ws_client.ws_client import WsClient
import queue
from utils.config_manager import ConfigManager
from utils.ai_analyzer import AiAnalyzer
from utils.db_utils import DatabaseManager

class JobHandler(threading.Thread):
    def __init__(self, job_queue: queue.Queue, ws_queue: queue.Queue, done_event, running_event, ):
        super().__init__(daemon=True,name="job_hander")
        self.job_queue = job_queue
        self.ws_queue = ws_queue
        self.done_event = done_event
        self.running_event = running_event
        self.loop = None

        config = ConfigManager.get_config()
        self.ai_analyzer = AiAnalyzer()
        crawler_config = config.crawler
        self.rate_limit = TokenBucket(rate=crawler_config.rate_limit["rate"], capacity=crawler_config.rate_limit["capacity"])
        self.db_manager = DatabaseManager(config.database.filename)
        self.inactive_keywords = config.job_check.inactive_status
        self.resume_image_enabled = config.application.send_resume_image
        self.min_salary, self.max_salary = config.job_check.salary_range
        self.check_visited = config.job_check.check_visited
        self.cookies= {}
        self.headers = {}

    async def _original_process_single_job(self, job_data):
        result = {
            'job_id': None,
            'job_data': None,
            'analysis_result': None,
            'applied_result': None,
            'analysis_think': None
        }
        # 解析job_link中的参数
        link = job_data['job_link']
        job_id, lid, security_id = parse_params(link)
        result['job_id'] = job_id
        # 实际的请求处理逻辑
        try:
            # 获取职位详细信息（限速）
            await self.rate_limit.get_token()  # 限速调用
            job_detail = await get_job_info(security_id, lid)
            result['job_data'] = job_detail
            # 检查HR活跃状态
            active_status = job_detail['zpData']['jobCard'].get('activeTimeDesc', '')
            if active_status in self.inactive_keywords:
                logger.info(f"跳过{job_data['job_name']}：HR活跃状态[{active_status}]不符合要求")
                return result

            # 构建岗位要求
            card = job_detail['zpData']['jobCard']
            job_requirements = (
                f"公司名称：{card['brandName']}\n"
                f"职位名称：{card['jobName']}\n"
                f"岗位职责：{card['postDescription']}\n"
                f"经验要求：{card['experienceName']}\n"
                f"学历要求：{card['degreeName']}"
            )

            # 不限速调用
            ai_result, ai_think = await self.ai_analyzer.ai_hr_check(job_requirements)
            result['analysis_result'] = ai_result
            if ai_think:
                result['analysis_think'] = ai_think
                logger.info(ai_think)


            if ai_result:
                # 判断是否启用 AI 打招呼语
                greeting_message = None
                if self.ai_analyzer.greeting_enable_ai:
                    # 调用 ai_greeting 方法获取打招呼语
                    greeting_message = await self.ai_analyzer.ai_greeting(job_requirements)
                    logger.info(f"job {job_data['job_name']}: 打招呼语： {greeting_message}")

                # 限速调用
                await self.rate_limit.get_token()  # 限速调用
                apply_result = await start_chat(security_id, job_id, lid)

                if greeting_message:
                    # 将打招呼语作为文本消息发送到 ws_client
                    self.ws_queue.put(["task", ("msg", card["securityId"], card["encryptUserId"], greeting_message)])

                # 还可以放入自定义信息
                if self.resume_image_enabled:
                    self.ws_queue.put(["task",("image", card["securityId"],card["encryptUserId"], "")])
                logger.info(f"job {job_data['job_name']}: {apply_result['message']}\n{job_requirements}\n\n")
            else:
                logger.info(f"job {job_data['job_name']}: ai认为不匹配\n{job_requirements}\n\n")

            return result

        except Exception as e:
            logger.error(
                f"Error processing job {job_data['job_name']}, {job_id}:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return result

    async def _process_single_job(self, job_data):
        try:
            return await asyncio.wait_for(
                self._original_process_single_job(job_data),
                timeout=240.0  # 每个任务单独超时
            )
        except asyncio.TimeoutError:
            logger.info(f"Job {job_data['job_name']} 被强制取消")
            return None
        except asyncio.CancelledError:
            logger.info(f"Job {job_data['job_name']} 收到取消信号")  # 关键日志
            # 必须重新抛出保证取消传播
            #raise
            return None

    async def _process_batch(self, jobs_batch):
        tasks = [self._process_single_job(job) for job in jobs_batch]
        return await asyncio.gather(*tasks)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        while self.running_event.is_set():
            batch = self.job_queue.get()
            if batch[0]=="tasks":
                self.done_event.clear()
                _, jobs_batch = batch
                # 满足薪资要求的岗位
                filter_salary_jobs = filter_jobs_by_salary(jobs_batch, self.min_salary, self.max_salary)
                
                filtered_jobs = filter_salary_jobs
                if self.check_visited:
                    # 未被访问过的岗位
                    filtered_jobs = self.db_manager.filter_visited(filter_salary_jobs)
                
                results = []
                if filtered_jobs:
                    try:
                        results = self.loop.run_until_complete(
                            asyncio.wait_for(
                                self._process_batch(filtered_jobs),
                                timeout=900  # 单位：秒
                            )
                        )
                        logger.info(f"Processed batch with {len(results)} jobs")
                        results = [result for result in results if result is not None]
                    except asyncio.TimeoutError:
                        logger.info("Batch processing timed out after 600 seconds")
                        results = []
                self.db_manager.save_jobs_details(jobs_batch, results)
                self.done_event.set()
                self.job_queue.task_done()
