# src/common/db_manager.py
import logging
import json
from datetime import datetime
from typing import List, Dict, Set

from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, inspect, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# 使用 SQLAlchemy 的 ORM 定义
Base = declarative_base()

class JobDetail(Base):
    """
    职位详情的数据模型，映射到数据库中的 'job_details' 表。
    该模型来自原始代码，以保留详细的字段结构。
    """
    __tablename__ = 'job_details'
    # 主键和唯一标识
    encryptJobId = Column(String(64), primary_key=True)
    
    # 核心职位信息
    jobName = Column(String(128))
    salaryDesc = Column(String(128))
    companyName = Column(String(128))
    postDescription = Column(Text)
    
    # 工作地点信息
    cityName = Column(String(64))
    address = Column(String(256))
    
    # 职位要求
    experienceName = Column(String(64))
    degreeName = Column(String(64))
    
    # 公司/职位标签 (以JSON字符串形式存储)
    companyTags = Column(Text)
    jobLabels = Column(Text)
    
    # Boss直聘平台特有信息
    lid = Column(String(64))
    securityId = Column(String(64))
    encryptUserId = Column(String(64))
    
    # Boss信息
    bossName = Column(String(64))
    bossTitle = Column(String(64))
    bossAvatar = Column(String(256))
    activeTimeDesc = Column(String(64), default="")
    
    # 系统状态字段
    visited = Column(Boolean, default=False)
    analysisResult = Column(Boolean)
    applied_account = Column(Text) # 投递该职位的账户
    updateTime = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    first_added_time = Column(DateTime, default=datetime.now) # 首次获取职位时的日期
    analysis_think = Column(Text) # AI分析的思考过程


class DatabaseManager:
    """
    数据库管理类 (使用 SQLAlchemy ORM)
    以单例模式运行，通过事件订阅来处理数据库操作。
    """
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
        """
        检查并创建数据库表。
        """
        try:
            with self.engine.begin() as conn:
                # 使用 Base.metadata 创建所有定义的表
                Base.metadata.create_all(conn)
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
            raise

    def check_jobs_exist(self, job_ids: List[str]) -> Set[str]:
        """
        批量检查职位ID是否已存在于数据库中。
        """
        if not job_ids:
            return set()
        
        with self.Session() as session:
            try:
                # 查询已存在的职位ID
                query_result = session.query(JobDetail.encryptJobId).filter(JobDetail.encryptJobId.in_(job_ids)).all()
                # 将结果转换为一个集合，方便快速查找
                return {row[0] for row in query_result}
            except Exception as e:
                logger.error(f"查询职位是否存在时出错: {e}", exc_info=True)
                return set()

    async def save_initial_jobs(self, jobs: List[Dict], **kwargs):
        """
        事件订阅函数：保存初次获取的职位列表基本信息。
        使用 session.merge 实现插入或更新操作。
        """
        if not jobs:
            return
        
        logger.info(f"数据库收到 {len(jobs)} 个职位信息，准备进行批量保存...")
        now = datetime.now()
        
        with self.Session() as session:
            try:
                for job in jobs:
                    job_card = job.get('jobCard', {})
                    if not job_card.get('encryptJobId'):
                        continue

                    # 将API数据映射到JobDetail模型
                    job_record = JobDetail(
                        encryptJobId=job_card.get('encryptJobId'),
                        jobName=job_card.get('jobName'),
                        salaryDesc=job_card.get('salaryDesc'),
                        companyName=job_card.get('brandName'),
                        cityName=job_card.get('cityName'),
                        experienceName=job_card.get('experienceName'),
                        degreeName=job_card.get('degreeName'),
                        jobLabels=json.dumps(job_card.get('jobLabels', []), ensure_ascii=False),
                        companyTags=json.dumps(job_card.get('skills', []), ensure_ascii=False),
                        lid=job.get('lid'),
                        securityId=job.get('securityId'),
                        encryptUserId=job_card.get('encryptUserId'),
                        bossName=job_card.get('bossName'),
                        bossTitle=job_card.get('bossTitle'),
                        bossAvatar=job_card.get('bossAvatar'),
                        activeTimeDesc=job_card.get('activeTimeDesc'),
                        first_added_time=now,
                        updateTime=now,
                        visited=False # 初始状态为未访问
                    )
                    # session.merge()会根据主键判断是插入还是更新
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
        job_info = analysis_data.get("job_info", {})
        job_card = job_info.get("jobCard", {})
        encrypt_job_id = job_card.get("encryptJobId")
        if not encrypt_job_id:
            return

        with self.Session() as session:
            try:
                # 查找需要更新的职位记录
                job_to_update = session.query(JobDetail).filter_by(encryptJobId=encrypt_job_id).first()
                if job_to_update:
                    job_to_update.analysisResult = analysis_data['is_match']
                    job_to_update.analysis_think = analysis_data['think_process']
                    job_to_update.updateTime = datetime.now()
                    # 注意：新架构下职位详情数据（如postDescription）不在分析阶段获取
                    # 如果需要，应修改JobAnalyzer来获取完整数据
                    if job_card.get('postDescription'):
                         job_to_update.postDescription = job_card.get('postDescription')
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
        job_card = job_data.get("jobCard", {})
        encrypt_job_id = job_card.get("encryptJobId")
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
        关闭数据库连接（在程序退出时调用）。
        """
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接池已关闭")