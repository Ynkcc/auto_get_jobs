import logging
logger = logging.getLogger(__name__)
import traceback
import asyncio
from utils.async_utils import *
from utils.general import parseParams
from ws_client.ws_client import WSclient
import queue
from utils.config_manager import ConfigManager

class JobProcessor:
    def __init__(self, comm_queue: queue.Queue, recv_queue: queue.Queue, done_event, resume_image_dict):
        self.comm_queue = comm_queue
        self.recv_queue = recv_queue
        self.done_event = done_event
        self.loop = None

        config = ConfigManager.get_config()
        self.ai_analyzer = AIAnalyzer(config.ai)
        self.crawler = config.crawler
        self.rate_limit = TokenBucket(rate=self.crawler.rate_limit["rate"], capacity=self.crawler.rate_limit["capacity"])

        self.inactive_keywords = config.job_check.inactive_status
        self.resume_image_dict = resume_image_dict

    async def _original_process_single_job(self, job_data, cookies, headers):
        result = {
            'job_id': None,
            'job_data': None,
            'analysis_result': None,
            'applied_result': None,
            'analysis_think': None
        }
        # 解析job_link中的参数
        link = job_data['job_link']
        job_id, lid, security_id = parseParams(link)
        result['job_id'] = job_id
        # 实际的请求处理逻辑
        try:
            # 获取职位详细信息（限速）
            await self.rate_limit.get_token()  # 限速调用
            job_detail = await getJobInfo(security_id, lid, cookies, headers)
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
            ai_result, ai_think = await self.ai_analyzer.aiHrCheck(job_requirements)
            result['analysis_result'] = ai_result
            if ai_think:
                result['analysis_think'] = ai_think
                logger.info(ai_think)

            if ai_result:
                # 限速调用
                await self.rate_limit.get_token()  # 限速调用
                apply_result = await startChat(security_id, job_id, lid, cookies, headers)
                # 还可以放入自定义信息
                if self.resume_image_dict:
                    self.ws_queue.put(("image", card["encryptUserId"], ""))
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

    async def _process_single_job(self, job_data, cookies, headers):
        try:
            return await asyncio.wait_for(
                self._original_process_single_job(job_data, cookies, headers),
                timeout=120.0  # 每个任务单独超时
            )
        except asyncio.TimeoutError:
            logger.info(f"Job {job_data['job_name']} 被强制取消")
            return None
        except asyncio.CancelledError:
            logger.info(f"Job {job_data['job_name']} 收到取消信号")  # 关键日志
            # 必须重新抛出保证取消传播
            #raise
            return None

    async def _process_batch(self, jobs_batch, cookies, headers):
        tasks = [self._process_single_job(job, cookies, headers) for job in jobs_batch]
        return await asyncio.gather(*tasks)

    def start_processing(self):
        self.loop = asyncio.new_event_loop()
        self.ws_queue = queue.Queue()
        self.ws_running_event = threading.Event()
        self.ws_client = None
        asyncio.set_event_loop(self.loop)

        while True:
            batch = self.comm_queue.get()
            if batch is None:  # 终止信号
                self.done_event.set()
                break

            # 提取 cookies 和 headers
            cookies = batch.get("cookies")
            headers = batch.get("headers")
            jobs_batch = batch.get("jobs")

            # 初始化WebSocket客户端
            if not self.ws_client:
                self.ws_client = WSclient(
                    recv_queue=self.ws_queue,
                    running_event=self.ws_running_event,
                    image_dict=self.resume_image_dict,
                    headers=headers,
                    cookies=cookies
                )

                self.ws_client.start()

            try:
                results = self.loop.run_until_complete(
                    asyncio.wait_for(
                        self._process_batch(jobs_batch, cookies, headers),
                        timeout=600  # 单位：秒
                    )
                )
                logger.info(f"Processed batch with {len(results)} jobs")
            except asyncio.TimeoutError:
                logger.info("Batch processing timed out after 600 seconds")
                results = []  # 超时后的处理逻辑
            results = [result for result in results if result is not None]
            self.recv_queue.put(results)
            self.done_event.set()  # 通知主进程处理完成