# src/core/job_analyzer.py
import logging
import asyncio
from ..services.ai_analyzer import AiAnalyzer
# 移除了 filter_jobs_by_salary 的导入，因为前置筛选已完成
from ..common.event_manager import event_manager
from ..common.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class JobAnalyzer:
    """负责职位的AI分析功能"""

    def __init__(self, config):
        self.config = config
        self.ai_analyzer = AiAnalyzer()
        self.db_manager = DatabaseManager(config.database.filename)


    async def process_job_list(self, jobs: list, **kwargs):
        """
        事件订阅函数：处理前置筛选后的职位列表。
        """
        logger.info(f"JobAnalyzer 收到 {len(jobs)} 个已筛选职位进行AI分析")

        # 数据库去重 (过滤掉在以往运行中已存入数据库的职位)
        job_ids = [job['jobCard']['encryptJobId'] for job in jobs if job.get('jobCard')]
        existing_ids = self.db_manager.check_jobs_exist(job_ids)
        unique_new_jobs = [job for job in jobs if job.get('jobCard') and job['jobCard']['encryptJobId'] not in existing_ids]

        if not unique_new_jobs:
            logger.info("没有新的符合条件的职位需要处理")
            return

        logger.info(f"过滤和去重后，有 {len(unique_new_jobs)} 个新职位待AI分析")
        tasks = [self.process_single_job(job) for job in unique_new_jobs]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_single_job(self, job_data: dict):
        """
        处理单个职位的AI分析
        """
        job_card = job_data.get("jobCard", {})
        encrypt_job_id = job_card.get("encryptJobId")
        job_name = job_card.get("jobName")
        
        if not encrypt_job_id:
            logger.warning("职位数据缺少 encryptJobId，无法处理")
            return

        try:
            logger.info(f"开始分析职位: {job_name} ({encrypt_job_id})")

            # 构建职位详情描述
            job_desc = self._build_job_description(job_data)

            # AI 分析
            is_match, think_process = await self.ai_analyzer.ai_hr_check(job_desc)

            # 准备要发布和存储的数据
            analysis_data = {
                "job_info": job_data,
                "is_match": is_match,
                "think_process": think_process or ""
            }

            # 发布分析完成事件，供DBManager更新数据库
            await event_manager.publish("job_analysis_complete", analysis_data=analysis_data)

            # 如果匹配，发布添加好友事件
            if is_match:
                logger.info(f"职位 '{job_name}' AI分析匹配成功，准备添加好友")
                # 将 securityId 传递下去，供后续使用
                await event_manager.publish("add_friend", job_data=job_data, securityId=job_data.get('securityId'))
            else:
                logger.info(f"职位 '{job_name}' AI分析不匹配")
        except Exception as e:
            logger.error(f"处理职位 '{job_name}' ({encrypt_job_id}) 时出错: {e}", exc_info=True)

    def _build_job_description(self, job_data: dict) -> str:
        """
        构建职位描述字符串用于AI分析
        """
        job_card = job_data.get('jobCard', {})

        job_desc = f"公司名称：{job_card.get('brandName', '')}\n"
        job_desc += f"职位名称：{job_card.get('jobName', '')}\n"
        # 岗位职责可能为空，需要判断
        post_desc = job_card.get('postDescription')
        if post_desc:
            job_desc += f"岗位职责：{post_desc}\n"
        
        job_desc += f"经验要求：{job_card.get('experienceName', '')}\n"
        job_desc += f"学历要求：{job_card.get('degreeName', '')}\n"
        job_desc += f"薪资：{job_card.get('salaryDesc', '')}"

        return job_desc

    async def close(self, **kwargs):
        """清理资源"""
        await self.ai_analyzer.close()
        logger.info("JobAnalyzer 已关闭")