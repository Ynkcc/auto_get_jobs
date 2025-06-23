# src/common/db_manager.py
import logging
import json
from datetime import datetime
from typing import List, Dict, Set

from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)
Base = declarative_base()

class JobDetail(Base):
    """职位详情的数据模型"""
    __tablename__ = 'job_details'
    encryptJobId = Column(String(64), primary_key=True)
    jobName = Column(String(128))
    salaryDesc = Column(String(128))
    companyName = Column(String(128))
    postDescription = Column(Text)
    cityName = Column(String(64))
    address = Column(String(256))
    experienceName = Column(String(64))
    degreeName = Column(String(64))
    companyTags = Column(Text)
    jobLabels = Column(Text)
    lid = Column(String(64))
    securityId = Column(String(64))
    encryptUserId = Column(String(64))
    bossName = Column(String(64))
    bossTitle = Column(String(64))
    bossAvatar = Column(String(256))
    activeTimeDesc = Column(String(64), default="")
    visited = Column(Boolean, default=False)
    analysisResult = Column(Boolean)
    applied_account = Column(Text)
    updateTime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    first_added_time = Column(DateTime, default=datetime.now)
    analysis_think = Column(Text)

class DatabaseManager:
    _instance = None

    def __new__(cls, db_name: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info(f"正在初始化数据库连接: {db_name}")
            cls._instance.engine = create_engine(f'sqlite:///{db_name}?check_same_thread=False')
            cls._instance.Session = sessionmaker(bind=cls._instance.engine)
            cls._instance._create_tables()
            logger.info("数据库初始化完成")
        return cls._instance

    def _create_tables(self):
        try:
            with self.engine.begin() as conn:
                Base.metadata.create_all(conn)
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
            raise

    def check_jobs_exist(self, job_ids: List[str]) -> Set[str]:
        if not job_ids:
            return set()
        with self.Session() as session:
            try:
                query_result = session.query(JobDetail.encryptJobId).filter(JobDetail.encryptJobId.in_(job_ids)).all()
                return {row[0] for row in query_result}
            except Exception as e:
                logger.error(f"查询职位是否存在时出错: {e}", exc_info=True)
                return set()

    async def save_initial_jobs(self, jobs: List[Dict], **kwargs):
        """
        事件订阅函数：保存完整的职位列表信息。
        """
        if not jobs:
            return
        
        logger.info(f"数据库收到 {len(jobs)} 个完整职位信息，准备进行批量保存...")
        now = datetime.now()
        
        with self.Session() as session:
            try:
                for job in jobs:
                    job_info = job.get('jobInfo', {})
                    boss_info = job.get('bossInfo', {})
                    brand_info = job.get('brandComInfo', {})

                    if not job_info.get('encryptId'):
                        continue

                    job_record = JobDetail(
                        encryptJobId=job_info.get('encryptId'),
                        jobName=job_info.get('jobName'),
                        salaryDesc=job_info.get('salaryDesc'),
                        companyName=brand_info.get('brandName'),
                        postDescription=job_info.get('postDescription'),
                        cityName=job_info.get('locationName'),
                        address=job_info.get('address'),
                        experienceName=job_info.get('experienceName'),
                        degreeName=job_info.get('degreeName'),
                        # 合并原始的 skills 和 showSkills
                        companyTags=json.dumps(job.get('skills', []) + job_info.get('showSkills', []), ensure_ascii=False),
                        jobLabels=json.dumps(job.get('jobLabels', []), ensure_ascii=False),
                        lid=job.get('lid'),
                        securityId=job.get('securityId'),
                        encryptUserId=boss_info.get('encryptUserId'),
                        bossName=boss_info.get('name'),
                        bossTitle=boss_info.get('title'),
                        bossAvatar=boss_info.get('tiny'),
                        activeTimeDesc=boss_info.get('activeTimeDesc'),
                        first_added_time=now,
                        updateTime=now,
                        visited=False
                    )
                    session.merge(job_record)
                
                session.commit()
                logger.info(f"成功向数据库中合并了 {len(jobs)} 条职位记录")
            except Exception as e:
                session.rollback()
                logger.error(f"批量保存职位时出错: {e}", exc_info=True)

    async def update_job_analysis(self, analysis_data: Dict, **kwargs):
        """
        事件订阅函数：更新职位的AI分析结果。
        """
        job_info = analysis_data.get("job_info", {}).get("jobInfo", {})
        encrypt_job_id = job_info.get("encryptId")
        if not encrypt_job_id:
            return

        with self.Session() as session:
            try:
                job_to_update = session.query(JobDetail).filter_by(encryptJobId=encrypt_job_id).first()
                if job_to_update:
                    job_to_update.analysisResult = analysis_data['is_match']
                    job_to_update.analysis_think = analysis_data['think_process']
                    job_to_update.updateTime = datetime.now()
                    # 确保 postDescription 也被更新
                    if job_info.get('postDescription'):
                         job_to_update.postDescription = job_info.get('postDescription')
                    session.commit()
                    logger.debug(f"成功更新职位 {encrypt_job_id} 的AI分析结果")
                else:
                    logger.warning(f"尝试更新分析结果，但未在数据库中找到职位ID: {encrypt_job_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"更新职位分析结果时出错: {e}", exc_info=True)

    async def update_job_status_applied(self, job_data: dict, **kwargs):
        """
        事件订阅函数：更新职位状态为“已投递”。
        """
        encrypt_job_id = job_data.get("jobInfo", {}).get("encryptId")
        if not encrypt_job_id:
            return
            
        with self.Session() as session:
            try:
                job_to_update = session.query(JobDetail).filter_by(encryptJobId=encrypt_job_id).first()
                if job_to_update:
                    job_to_update.visited = True
                    job_to_update.updateTime = datetime.now()
                    session.commit()
                    logger.debug(f"成功更新职位 {encrypt_job_id} 的状态为已投递 (visited=True)")
                else:
                    logger.warning(f"尝试更新投递状态，但未在数据库中找到职位ID: {encrypt_job_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"更新职位为'applied'状态时出错: {e}", exc_info=True)

    def close(self):
        """
        关闭数据库连接。
        """
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接池已关闭")