# database_utils.py
import logging
logger = logging.getLogger(__name__)
from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, inspect, DDL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from typing import List, Optional, Dict, Any
import re

Base = declarative_base()

class JobDetail(Base):
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
    
    # 公司/职位标签
    companyTags = Column(Text)  # JSON字符串
    jobLabels = Column(Text)  # JSON字符串
    
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
    analysisResult = Column(Boolean, default=False) #没分析/不匹配都是False #TODO
    applied_account = Column(Text)
    updateTime = Column(DateTime, default=datetime.now)


class DatabaseManager:
    """数据库管理类，提供优化的CRUD操作"""
    
    def __init__(self, db_path: str, userId: str):
        self.engine = create_engine(f'sqlite:///{db_path}', pool_pre_ping=True)
        self._create_tables()
        self.Session = sessionmaker(bind=self.engine)
        self.userId = userId

    def _create_tables(self):
        """确保表结构存在并自动添加新增列"""
        with self.engine.begin() as conn:
            inspector = inspect(conn)
            table_name = JobDetail.__tablename__
            
            # 创建表（如果不存在）
            if not inspector.has_table(table_name):
                Base.metadata.create_all(conn)
            # 表结构变更 #TODO


    def save_jobs_details(self, jobs: List[Dict], jobs_details: List[Dict]) -> None:
        """
        保存工作详情及基础数据，进行插入或更新操作
        """
        if not jobs:
            raise ValueError("jobs不能为空")
        if not jobs_details:
            jobs_details = []
        with self.Session() as session:
            try:
                # 构建基础数据字典
                job_dict = {
                    self.parseParams(job["job_link"])[0]: self._build_base_job(job)
                    for job in jobs
                }

                # 合并详细数据
                records = []
                processed_ids=set()
                for detail in jobs_details:
                    if not isinstance(detail, dict):  # 类型安全检查
                        detail = json.loads(detail)
                    
                    try:
                        card = detail.get('job_data', {}).get('zpData', {}).get('jobCard')
                        eid = card.get('encryptJobId')
                    except:
                        logger.error(f'{detail["job_id"]},不含详细信息')
                        continue
                    
                    # 记录已处理ID
                    processed_ids.add(eid)
                    
                    # 合并基础数据和详细数据
                    record = job_dict.get(eid, {})
                    record.update(self._build_detail_data(card, detail))
                    records.append(record)

                # 新增：补充未处理的纯基础数据（仅当有基础数据且无详细数据时）
                for eid, base_data in job_dict.items():
                    if eid not in processed_ids:
                        # 确保基础数据有效性
                        if base_data.get('encryptJobId') and base_data.get('jobName'):
                            records.append(base_data)
                self._upsert_records(session, [r for r in records if r.get('encryptJobId')])
                session.commit()
                
            except Exception as e:
                session.rollback()
                raise RuntimeError(f"数据保存失败: {str(e)}")

    def _build_base_job(self, job: Dict) -> Dict:
        """构建基础数据记录"""
        encryptJobId, lid, securityId = self.parseParams(job["job_link"])
        return {
            'jobName': job.get('job_name'),
            'salaryDesc': job.get('job_salary'),
            'companyName': job.get('company_name'),
            'companyTags': json.dumps(job.get('company_tags', []), ensure_ascii=False),
            'encryptJobId': encryptJobId,
            'lid': lid,
            'securityId': securityId,
            'updateTime':datetime.now()
        }

    def _build_detail_data(self, card: Dict, detail: Dict) -> Dict:
        """构建详细数据记录"""
        return {
            'postDescription': card.get('postDescription'),
            'cityName': card.get('cityName'),
            'experienceName': card.get('experienceName'),
            'degreeName': card.get('degreeName'),
            'jobLabels': json.dumps(card.get('jobLabels', []), ensure_ascii=False),
            'address': card.get('address', ''),
            'encryptUserId': card.get('encryptUserId'),
            'bossName': card.get('bossName'),
            'bossTitle': card.get('bossTitle'),
            'bossAvatar': card.get('bossAvatar', ''),
            'analysisResult':detail.get("analysis_result"),
            'applied_account': self.userId,#用户id
            'visited': True,
            "activeTimeDesc":card.get("activeTimeDesc")
        }

    def _upsert_records(self, session, records: List[Dict]) -> None:
        """插入或更新记录"""
        for record in records:
            if not record.get('encryptJobId'):
                continue

            # 判断该记录是否已存在
            existing = session.query(JobDetail).filter_by(encryptJobId=record['encryptJobId']).first()

            if existing:
                # 更新现有记录
                for key, value in record.items():
                    setattr(existing, key, value)
            else:
                # 插入新记录
                new_record = JobDetail(**record)
                session.add(new_record)
    @staticmethod
    def parseParams(link):
        """
        从招聘链接中提取关键参数
        """
        pattern = r'/job_detail/([^.]+)\.html\?lid=([^&]+)&securityId=([^&]+)'
        match = re.search(pattern, link)
        return match.groups() if match else None

    def check_visited(self, job_id):
        session = self.Session()
        try:
            job = session.query(JobDetail).get(job_id)
            return job.visited if job else False
        finally:
            session.close()
    def check_visited(self, job_id,user_id:str):
        session = self.Session()
        try:
            job = session.query(JobDetail).get(job_id)
            return (job.visited if job else False) and (str(user_id) in job.applied_account)
        finally:
            session.close()
    def filterVisited(self,jobs):
        filteredJobs=[]
        for job in jobs:
            job_name = job['job_name']
            job_id = self.parseParams(job["job_link"])[0]
            checkResult=self.check_visited(job_id)
            if checkResult:
                logger.info(f"已经访问过 招聘岗位: {job_name}")
            else:
                filteredJobs.append(job)
        return filteredJobs

    def filterVisited(self,jobs,user_id):
        filteredJobs=[]
        for job in jobs:
            job_name = job['job_name']
            job_id = self.parseParams(job["job_link"])[0]
            checkResult=self.check_visited(job_id,user_id)
            if checkResult:
                logger.info(f"该账号已经访问过 招聘岗位: {job_name}")
            else:
                filteredJobs.append(job)
        return filteredJobs