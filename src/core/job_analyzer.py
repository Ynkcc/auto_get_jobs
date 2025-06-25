# src/core/job_analyzer.py
import logging
import asyncio
from ..services.ai_analyzer import AiAnalyzer
from ..common.event_manager import event_manager
from ..common.db_manager import DatabaseManager
from ..services.zhipin_api import zhipin_api

logger = logging.getLogger(__name__)

class JobAnalyzer:
    """负责职位的详情获取和AI分析功能"""

    def __init__(self, config):
        self.config = config
        self.ai_analyzer = AiAnalyzer()
        self.db_manager = DatabaseManager(config.database.filename)
        self.analyzed_job_ids = set() # 内存去重，避免重复分析

    async def fetch_job_details(self, jobs: list, **kwargs):
        """
        事件订阅函数：接收初步的职位列表，并获取每个职位的完整信息。
        """
        logger.info(f"JobAnalyzer 收到 {len(jobs)} 个基本职位信息，开始获取详细信息...")
        
        async def get_detail(job):
            security_id = job.get('securityId')
            lid = job.get('lid')
            if not security_id or not lid:
                return None
            
            detail_data = await zhipin_api.get_job_detail(security_id, lid)
            if detail_data:
                # 合并基础信息和详细信息
                merged_data = job.copy()
                merged_data.update(detail_data)
                return merged_data
            return None

        tasks = [get_detail(job) for job in jobs]
        full_job_details = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉获取失败和异常的结果
        valid_jobs = [j for j in full_job_details if j and not isinstance(j, Exception)]
        
        if not valid_jobs:
            logger.warning("未能获取到任何职位的详细信息")
            return
            
        logger.info(f"成功获取了 {len(valid_jobs)}/{len(jobs)} 个职位的详细信息")
        await event_manager.publish("job_details_fetched", jobs=valid_jobs)


    async def process_job_list(self, jobs: list, **kwargs):
        """
        事件订阅函数：处理前置筛选后的【完整】职位列表。
        """
        logger.info(f"JobAnalyzer 收到 {len(jobs)} 个已筛选职位进行AI分析")

        unique_new_jobs = []
        for job in jobs:
            job_info = job.get('jobInfo', {})
            encrypt_job_id = job_info.get('encryptId')
            if encrypt_job_id and encrypt_job_id not in self.analyzed_job_ids:
                 unique_new_jobs.append(job)
                 self.analyzed_job_ids.add(encrypt_job_id)

        if not unique_new_jobs:
            logger.info("没有新的符合条件的职位需要分析")
            return

        logger.info(f"内存去重后，有 {len(unique_new_jobs)} 个新职位待AI分析")
        tasks = [self.process_single_job(job) for job in unique_new_jobs]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_single_job(self, job_data: dict):
        """
        处理单个职位的AI分析 (使用完整数据结构)
        """
        job_info = job_data.get("jobInfo", {})
        encrypt_job_id = job_info.get("encryptId")
        job_name = job_info.get("jobName")
        
        if not encrypt_job_id:
            logger.warning("职位数据缺少 encryptJobId，无法处理")
            return

        try:
            logger.info(f"开始分析职位: {job_name} ({encrypt_job_id})")

            job_desc = self._build_job_description(job_data)
            is_match, think_process = await self.ai_analyzer.ai_hr_check(job_desc)

            analysis_data = {
                "job_info": job_data,
                "is_match": is_match,
                "think_process": think_process or ""
            }

            await event_manager.publish("job_analysis_complete", analysis_data=analysis_data)

            if is_match:
                logger.info(f"职位 '{job_name}' AI分析匹配成功，准备生成打招呼语并发起沟通")
                # 生成打招呼语
                greeting = await self.ai_analyzer.ai_greeting(job_desc)
                if not greeting:
                    logger.warning(f"未能为职位 '{job_name}' 生成打招呼语，将使用默认。")
                    # 如果需要，可以在这里设置一个默认打招呼语
                
                # 将打招呼语添加到数据中，并发布事件
                await event_manager.publish("add_friend", job_data=job_data, greeting_message=greeting)
            else:
                logger.info(f"职位 '{job_name}' AI分析不匹配")
        except Exception as e:
            logger.error(f"处理职位 '{job_name}' ({encrypt_job_id}) 时出错: {e}", exc_info=True)

    def _build_job_description(self, job_data: dict) -> str:
        """
        从【完整】职位数据构建描述字符串用于AI分析
        """
        job_info = job_data.get('jobInfo', {})
        brand_info = job_data.get('brandComInfo', {})

        job_desc = f"公司名称：{brand_info.get('brandName', '')}\n"
        job_desc += f"职位名称：{job_info.get('jobName', '')}\n"
        post_desc = job_info.get('postDescription')
        if post_desc:
            job_desc += f"岗位职责：{post_desc}\n"
        
        job_desc += f"经验要求：{job_info.get('experienceName', '')}\n"
        job_desc += f"学历要求：{job_info.get('degreeName', '')}\n"
        job_desc += f"薪资：{job_info.get('salaryDesc', '')}"

        return job_desc

    async def close(self, **kwargs):
        """清理资源"""
        await self.ai_analyzer.close()
        logger.info("JobAnalyzer 已关闭")