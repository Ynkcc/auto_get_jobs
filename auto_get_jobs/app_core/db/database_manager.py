# app_core/db/database_manager.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from typing import List, Optional, Type

# 从模型文件中导入Base和Job, JobStatus
from app_core.models.job import Base, Job, JobStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_uri: str):
        logger.info(f"初始化数据库管理器，数据库URI: {database_uri}")
        try:
            self.engine = create_engine(database_uri)
            Base.metadata.create_all(self.engine)  # 创建所有表 (如果尚不存在)
            # 使用scoped_session来确保线程安全
            self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
            logger.info("数据库表结构已准备就绪。")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
            raise

    @contextmanager
    def get_db_session(self):
        """
        提供一个数据库会话上下文管理器。
        使用此方法来获取一个会话，并在完成后自动关闭。
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"数据库会话操作发生错误: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
            self.SessionLocal.remove() # 非常重要，移除当前线程的session

    def clear_all_data(self):
        """清空所有表的数据 (谨慎使用!)"""
        logger.warning("正在清空数据库中的所有数据...")
        with self.get_db_session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            # 如果使用SQLite，可能还需要 VACUUM 来回收空间，但这里省略
        logger.info("数据库已清空。")

    # --- Job 相关的 CRUD 操作 ---
    def add_job(self, job_data: dict) -> Optional[Job]:
        """添加一个新职位到数据库"""
        # 确保 job_data 中的 status 是 JobStatus 枚举类型
        if 'status' in job_data and isinstance(job_data['status'], str):
            try:
                job_data['status'] = JobStatus(job_data['status'])
            except ValueError:
                logger.warning(f"无效的职位状态字符串: {job_data['status']}，将使用默认值。")
                job_data['status'] = JobStatus.NEW


        # 检查是否存在相同 job_id 和 source_platform 的职位
        existing_job = self.get_job_by_job_id_and_platform(
            job_data.get("job_id"),
            job_data.get("source_platform")
        )
        if existing_job:
            logger.info(f"职位 {job_data.get('job_id')} ({job_data.get('source_platform')}) 已存在，跳过添加。")
            return existing_job # 或选择更新它

        new_job = Job(**job_data)
        with self.get_db_session() as db:
            db.add(new_job)
            # commit 会在 get_db_session 的 context manager 中处理
        logger.info(f"已添加新职位: {new_job.job_title} ({new_job.job_id})")
        return new_job

    def get_job_by_id(self, job_pk_id: int) -> Optional[Job]:
        """通过主键ID获取职位"""
        with self.get_db_session() as db:
            return db.query(Job).filter(Job.id == job_pk_id).first()

    def get_job_by_job_id_and_platform(self, job_id_str: str, platform: str) -> Optional[Job]:
        """通过职位网站的ID和平台获取职位"""
        if not job_id_str or not platform:
            return None
        with self.get_db_session() as db:
            return db.query(Job).filter(Job.job_id == job_id_str, Job.source_platform == platform).first()

    def update_job_status(self, job_pk_id: int, new_status: JobStatus, details: Optional[dict] = None) -> Optional[Job]:
        """更新职位状态和其他可选信息"""
        with self.get_db_session() as db:
            job = db.query(Job).filter(Job.id == job_pk_id).first()
            if job:
                old_status_str = str(job.status)
                job.status = new_status
                if details: # 更新其他字段
                    for key, value in details.items():
                        if hasattr(job, key):
                            setattr(job, key, value)
                # commit 在 context manager 中处理
                logger.info(f"职位 {job.job_title} (ID: {job.id}) 状态从 {old_status_str} 更新为 {new_status}")
                return job
            logger.warning(f"尝试更新状态失败：未找到PK ID为 {job_pk_id} 的职位。")
            return None

    def get_jobs_by_status(self, status_list: List[JobStatus], limit: int = 100, offset: int = 0) -> List[Job]:
        """根据一个或多个状态获取职位列表 (分页)"""
        with self.get_db_session() as db:
            query = db.query(Job).filter(Job.status.in_(status_list)).order_by(Job.updated_at.desc())
            return query.offset(offset).limit(limit).all()
            
    def get_all_jobs(self, limit: int = 1000, offset: int = 0) -> List[Job]:
        """获取所有职位 (主要用于测试或管理)"""
        with self.get_db_session() as db:
            return db.query(Job).order_by(Job.id.desc()).offset(offset).limit(limit).all()

    def count_jobs_by_status(self, status: JobStatus) -> int:
        """计算特定状态的职位数量"""
        with self.get_db_session() as db:
            return db.query(Job).filter(Job.status == status).count()

    def close(self):
        """关闭数据库引擎 (通常在应用关闭时调用)"""
        if self.engine:
            logger.info("正在关闭数据库引擎...")
            self.engine.dispose()
            logger.info("数据库引擎已关闭。")

if __name__ == '__main__':
    # 测试 DatabaseManager
    # 使用内存数据库进行测试
    db_manager = DatabaseManager('sqlite:///:memory:')

    # 添加职位
    job1_data = {
        "job_id": "pm001", "job_title": "Product Manager", "source_platform": "TestPlatform",
        "source_url": "http://example.com/pm001", "job_description": "Manage product."
    }
    job2_data = {
        "job_id": "dev002", "job_title": "Developer", "source_platform": "TestPlatform",
        "source_url": "http://example.com/dev002", "job_description": "Develop things.", "status": JobStatus.MATCHED
    }
    job1 = db_manager.add_job(job1_data)
    job2 = db_manager.add_job(job2_data)

    print(f"添加的职位1: {job1}")
    print(f"添加的职位2: {job2}")

    # 再次尝试添加已存在的职位
    db_manager.add_job(job1_data)


    # 获取职位
    ret_job1 = db_manager.get_job_by_id(job1.id)
    print(f"通过PK ID获取的职位1: {ret_job1.job_title}, 状态: {ret_job1.status}")

    # 更新状态
    db_manager.update_job_status(job1.id, JobStatus.ANALYZING, details={"ai_match_score": 75})
    updated_job1 = db_manager.get_job_by_id(job1.id)
    print(f"更新后的职位1: {updated_job1.job_title}, 状态: {updated_job1.status}, 分数: {updated_job1.ai_match_score}")

    # 按状态获取职位
    new_jobs = db_manager.get_jobs_by_status([JobStatus.ANALYZING])
    print(f"分析中的职位数量: {len(new_jobs)}")
    for j in new_jobs:
        print(f" - {j.job_title}")
        
    matched_jobs_count = db_manager.count_jobs_by_status(JobStatus.MATCHED)
    print(f"匹配状态的职位数量: {matched_jobs_count}")

    # 清空数据
    # db_manager.clear_all_data()
    # all_jobs_after_clear = db_manager.get_all_jobs()
    # print(f"清空后职位数量: {len(all_jobs_after_clear)}")

    db_manager.close()
