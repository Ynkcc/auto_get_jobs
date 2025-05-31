# app_core/models/job.py
import enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class JobStatus(enum.Enum):
    """
    职位状态枚举
    """
    NEW = "未处理"  # 新抓取的职位，尚未进行任何处理
    ANALYZING = "分析中"  # 正在被AI分析匹配度
    MATCHED = "匹配"  # AI分析结果为匹配
    UNMATCHED = "不匹配"  # AI分析结果为不匹配
    QUEUED_FOR_DELIVERY = "待投递" # 匹配后，或用户手动操作后，准备加入投递队列
    DELIVERING = "投递中"  # 正在通过WebSocket或其他方式进行投递
    DELIVERED = "已投递"  # 成功投递
    DELIVERY_FAILED = "投递失败" # 投递过程中发生错误
    USER_IGNORED = "用户忽略"  # 用户手动标记为忽略，不再处理
    USER_FILTERED = "用户过滤" # 用户手动标记为不匹配或从流程中移除
    ERROR = "处理错误"  # 在非投递环节发生未知错误
    # 可以根据需要添加更多状态，例如：
    # AWAITING_USER_ACTION = "等待用户操作"

    def __str__(self):
        return self.value

class Job(Base):
    """
    职位信息ORM模型
    """
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True, comment="来自招聘网站的职位ID") # 来自源网站的职位ID
    job_title = Column(String(255), nullable=False, comment="职位名称")
    company_name = Column(String(255), comment="公司名称")
    job_description = Column(Text, comment="职位描述原文")
    job_tags = Column(String(1000), comment="职位标签，逗号分隔") # 例如: "Python,SQL,Web开发"
    salary_range = Column(String(255), comment="薪资范围")
    location = Column(String(255), comment="工作地点")
    posted_date = Column(DateTime, comment="职位发布日期")
    source_url = Column(String(1024), nullable=False, comment="职位信息来源URL")
    source_platform = Column(String(255), comment="来源平台，如Liepin, Boss") # 例如: Liepin, Boss

    status = Column(Enum(JobStatus), default=JobStatus.NEW, nullable=False, index=True, comment="当前职位处理状态")
    ai_match_score = Column(Integer, comment="AI匹配度评分 (0-100)")
    ai_match_reason = Column(Text, comment="AI匹配/不匹配原因分析")
    ai_job_summary = Column(Text, comment="AI生成的职位摘要") # AI生成的职位摘要
    ai_resume_summary = Column(Text, comment="AI生成的简历相对于此职位的摘要") # AI生成的简历摘要 (针对此职位)

    # 投递相关信息
    delivery_attempts = Column(Integer, default=0, comment="尝试投递次数")
    last_delivery_attempt_at = Column(DateTime, comment="上次尝试投递时间")
    delivery_error_message = Column(Text, comment="投递失败时的错误信息") # 投递失败时的错误信息

    # 时间戳
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="记录创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, comment="记录更新时间")

    # 用户自定义字段
    user_notes = Column(Text, comment="用户备注") # 用户备注
    is_manual_override = Column(Boolean, default=False, comment="状态是否被用户手动覆盖过") # 标记状态是否被用户手动覆盖

    # 搜索参数信息 (关联到本次搜索的配置)
    search_param_name = Column(String(255), comment="本次职位抓取时使用的搜索参数名称") # 关联的搜索参数名
    search_city_name = Column(String(255), comment="本次职位抓取时使用的城市名称") # 关联的城市名

    __table_args__ = (
        Index('ix_job_status_updated_at', 'status', 'updated_at'), # 优化按状态和更新时间查询
    )

    def __repr__(self):
        return f"<Job(id={self.id}, job_id='{self.job_id}', title='{self.job_title}', status='{self.status}')>"

if __name__ == '__main__':
    # 这个部分仅用于测试模型定义，实际项目中由DatabaseManager处理引擎和会话
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    new_job = Job(
        job_id="test001",
        job_title="Python Developer",
        company_name="Test Corp",
        job_description="Looking for a Python dev...",
        source_url="http://example.com/job/test001",
        source_platform="ExampleSite",
        status=JobStatus.NEW
    )
    db.add(new_job)
    db.commit()

    retrieved_job = db.query(Job).filter_by(job_id="test001").first()
    print(retrieved_job)
    print(retrieved_job.status) # 输出: 未处理
    db.close()
