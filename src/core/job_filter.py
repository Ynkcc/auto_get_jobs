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

    async def pre_filter_jobs(self, jobs: list, **kwargs):
        """
        事件订阅函数：前置岗位筛选
        在AI分析前进行基础筛选，如薪资、工作描述关键字、公司名称等
        """
        logger.info(f"JobFilter 开始前置筛选 {len(jobs)} 个职位")
        
        # 1. 使用从 general.py 导入的函数进行薪资过滤
        salary_filtered_jobs = filter_jobs_by_salary(jobs, self.min_salary, self.max_salary)
        if len(jobs) != len(salary_filtered_jobs):
            logger.info(f"薪资过滤后剩余 {len(salary_filtered_jobs)} 个职位")

        final_filtered_jobs = []
        for job in salary_filtered_jobs:
            job_card = job.get('jobCard', {})

            # 2. 公司名称过滤（排除外包公司等）
            if not self._check_company_name(job_card):
                logger.debug(f"公司 {job_card.get('brandName')} 在排除列表中，已过滤")
                continue

            # 3. 工作描述关键字过滤 (可按需实现)
            if not self._check_job_description(job):
                logger.debug(f"职位 {job_card.get('jobName')} 描述不符合要求，已过滤")
                continue

            # 4. 检查是否已访问过
            # 注意: 此处检查数据库中是否存在，JobAnalyzer中会做更严格的内存去重
            if self.job_check_config.check_visited and self._is_job_visited(job_card):
                logger.debug(f"职位 {job_card.get('jobName')} 已在数据库中存在，已过滤")
                continue

            final_filtered_jobs.append(job)

        logger.info(f"前置筛选完成，{len(jobs)} -> {len(final_filtered_jobs)} 个职位通过筛选")

        # 发布筛选后的职位列表
        if final_filtered_jobs:
            await event_manager.publish("jobs_pre_filtered", jobs=final_filtered_jobs)

    def _check_company_name(self, job_card: dict) -> bool:
        """检查公司名称是否在排除列表中"""
        # 如果未在配置文件中启用该功能，则直接通过
        if not self.job_check_config.exclude_keywords or not self.job_check_config.exclude_keywords.company_name:
            return True

        company_name = job_card.get('brandName', '').lower()
        for keyword in self.job_check_config.exclude_keywords.company_name:
            if keyword.lower() in company_name:
                return False
        return True

    def _check_job_description(self, job: dict) -> bool:
        """检查工作描述是否包含必需/排除的关键字"""
        # 此处为扩展功能，可以根据配置添加更复杂的描述筛选逻辑
        # 示例:
        # job_card = job.get('jobCard', {})
        # description = job_card.get('postDescription', '').lower()
        # for keyword in self.job_check_config.exclude_keywords.job_description:
        #     if keyword.lower() in description:
        #         return False
        return True

    def _is_job_visited(self, job_card: dict) -> bool:
        """检查职位是否已经存在于数据库中"""
        encrypt_job_id = job_card.get('encryptJobId')
        if not encrypt_job_id:
            return False
        # check_jobs_exist 需要一个列表作为参数
        return bool(self.db_manager.check_jobs_exist([encrypt_job_id]))

    async def close(self, **kwargs):
        """清理资源"""
        logger.info("JobFilter 已关闭")