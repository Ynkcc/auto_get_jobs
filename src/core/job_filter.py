# src/core/job_filter.py
import logging
from ..common.event_manager import event_manager
from ..common.db_manager import DatabaseManager
from ..common.file_utils import filter_jobs_by_salary

logger = logging.getLogger(__name__)

class JobFilter:
    """负责职位的前置筛选功能"""

    def __init__(self, config):
        self.config = config
        self.job_check_config = config.job_check
        self.db_manager = DatabaseManager(config.database.filename)
        self.min_salary, self.max_salary = self.job_check_config.salary_range
        # 从配置中获取test_mode和inactive_status
        self.test_mode = self.job_check_config.test_mode
        self.inactive_keywords = self.job_check_config.inactive_status

    async def pre_filter_jobs(self, jobs: list, **kwargs):
        """
        事件订阅函数：前置岗位筛选 (基于完整职位信息)
        """
        logger.info(f"JobFilter 开始前置筛选 {len(jobs)} 个职位")
        
        # 根据测试模式决定是否进行薪资过滤
        if not self.test_mode:
            # 1. 非测试模式：执行薪资过滤
            logger.info("当前为非测试模式，执行薪资过滤。")
            job_infos_for_salary_check = [j.get('jobInfo', {}) for j in jobs]
            filtered_job_infos = filter_jobs_by_salary(job_infos_for_salary_check, self.min_salary, self.max_salary)
            
            filtered_job_ids = {info.get('encryptId') for info in filtered_job_infos}
            filtered_jobs = [job for job in jobs if job.get('jobInfo', {}).get('encryptId') in filtered_job_ids]

            if len(jobs) != len(filtered_jobs):
                logger.info(f"薪资过滤后剩余 {len(filtered_jobs)} 个职位")
        else:
            # 1. 测试模式：跳过薪资过滤
            logger.info("当前为测试模式，跳过薪资过滤。")
            filtered_jobs = jobs

        final_filtered_jobs = []
        for job in filtered_jobs:
            job_info = job.get('jobInfo', {})
            brand_info = job.get('brandComInfo', {})
            # 从 bossInfo 中获取HR活跃状态
            boss_info = job.get('bossInfo', {})
            active_status = boss_info.get('activeTimeDesc', '')

            # 2. HR活跃状态过滤（测试模式与非测试模式逻辑不同）
            if (active_status in self.inactive_keywords and not self.test_mode) or \
               (self.test_mode and active_status not in self.inactive_keywords):
                reason = f"测试模式下，活跃HR状态'{active_status}'被过滤" if self.test_mode else f"非测试模式下，不活跃HR状态'{active_status}'被过滤"
                logger.info(f"跳过职位 {job_info.get('jobName')}，原因: {reason}")
                continue

            # 3. 公司名称过滤
            if not self._check_company_name(brand_info):
                logger.debug(f"公司 {brand_info.get('brandName')} 在排除列表中，已过滤")
                continue

            # 4. 工作描述关键字过滤
            if not self._check_job_description(job_info):
                logger.debug(f"职位 {job_info.get('jobName')} 描述不符合要求，已过滤")
                continue

            # 5. 检查是否已在数据库中存在（已投递或已分析过）
            if self.job_check_config.check_visited and self._is_job_visited(job_info):
                logger.debug(f"职位 {job_info.get('jobName')} 已在数据库中存在，已过滤")
                continue

            final_filtered_jobs.append(job)

        logger.info(f"前置筛选完成，{len(jobs)} -> {len(final_filtered_jobs)} 个职位通过筛选")

        if final_filtered_jobs:
            await event_manager.publish("jobs_pre_filtered", jobs=final_filtered_jobs)

    def _check_company_name(self, brand_info: dict) -> bool:
        """检查公司名称是否在排除列表中"""
        if not self.job_check_config.exclude_keywords or not self.job_check_config.exclude_keywords.company_name:
            return True

        company_name = brand_info.get('brandName', '').lower()
        for keyword in self.job_check_config.exclude_keywords.company_name:
            if keyword.lower() in company_name:
                return False
        return True

    def _check_job_description(self, job_info: dict) -> bool:
        """检查工作描述是否包含必需/排除的关键字"""
        if not self.job_check_config.exclude_keywords or not self.job_check_config.exclude_keywords.job_description:
            return True
        
        description = job_info.get('postDescription', '').lower()
        for keyword in self.job_check_config.exclude_keywords.job_description:
            if keyword.lower() in description:
                return False
        return True



    def _is_job_visited(self, job_info: dict) -> bool:
        """检查职位是否已经存在于数据库中"""
        encrypt_job_id = job_info.get('encryptId')
        if not encrypt_job_id:
            return False
        return bool(self.db_manager.check_jobs_exist([encrypt_job_id]))

    async def close(self, **kwargs):
        """清理资源"""
        logger.info("JobFilter 已关闭")