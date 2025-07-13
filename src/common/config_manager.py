# src/common/config_manager.py
from pydantic import BaseModel, ValidationError, Field
from typing import Dict, Any, List, Optional
import yaml
import os
import shutil

class PlaywrightConfig(BaseModel):
    browser_type: str = Field(..., description="浏览器类型")
    custom_browser_path: str = Field(..., description="自定义浏览器路径")
    headless: bool = Field(..., description="无头模式 (后台运行)")
    use_default_data_dir: bool = Field(..., description="使用默认用户数据")
    scroll_pages: int = Field(3, description="默认滚动页数")

class AiProvider(BaseModel):
    id: str = Field(..., description="服务商唯一ID")
    name: str = Field(..., description="服务商名称")
    api_url: str = Field(..., description="API端点URL")
    api_key: str = Field(..., description="API密钥")
    model: str = Field(..., description="模型名称")
    temperature: float = Field(..., description="温度系数")
    provider_type: str = Field(..., description="API协议类型 (openai=OpenAI兼容接口, azure=Azure OpenAI)")
    api_version: Optional[str] = Field(None, description="API版本 (Azure需要)")

class AiConfig(BaseModel):
    active_ai_id: str = Field(..., description="当前使用的AI服务")
    providers: List[AiProvider] = Field(..., description="服务商列表")
    prompt: str = Field(..., description="AI分析核心提示词")
    job_requirements_prompt: str = Field(..., description="我的求职偏好")
    resume_for_ai_file: str = Field(..., description="简历文件路径 (用于AI分析)")
class RateLimitConfig(BaseModel):
    rate: float  # 每分钟请求次数
class CrawlerConfig(BaseModel):
    playwright: PlaywrightConfig = Field(..., description="浏览器核心设置")
    rate_limit: RateLimitConfig = Field(..., description="请求速率限制")
    next_page_delay: int = Field(..., description="翻页延迟 (秒)")
    request_timeout: int = Field(..., description="请求超时 (秒)")
    page_load_timeout: int = Field(..., description="页面加载超时 (秒)")

class GreetingConfig(BaseModel):
    enable_ai: bool = Field(..., description="启用AI生成问候语")
    greeting_prompt: str = Field(..., description="问候语生成提示词")
    greeting_for_ai_file: str = Field(..., description="问候语参考文件 (未实现)")

class ApplicationConfig(BaseModel):
    send_resume_image: bool = Field(..., description="自动发送简历图片")
    resume_image_file: str = Field(..., description="简历图片文件路径")
    greeting: GreetingConfig = Field(..., description="问候语设置")
    resume_name: str = Field(..., description="简历文件名称 (未实现)")

class LoggingConfig(BaseModel):
    level: str = Field(..., description="日志级别")
    path: str = Field(..., description="日志文件路径")
    max_size: int = Field(..., description="最大文件大小 (MB)")

class DatabaseConfig(BaseModel):
    filename: str = Field(..., description="数据库文件")
    export_excel: bool = Field(..., description="运行后导出到Excel")
    excel_path: str = Field(..., description="Excel导出目录")

class CityConfig(BaseModel):
    values: List[str] = Field(..., description="目标城市列表")
    expand_to_district: bool = Field(..., description="是否自动扩展到所有区域")

class MultiSelectConfig(BaseModel):
    values: List[int] = Field(default_factory=lambda: [0], description="选中的值")
    combine: bool = Field(True, description="是否合并为单次请求")

class JobSearchConfig(BaseModel):
    city: CityConfig = Field(..., description="目标城市")
    query: List[str] = Field(..., description="职位搜索关键词")
    areas: Dict[str, List[str]] = Field(..., description="目标区域 (城市: [区, ...])")
    # 使用新的多选配置模型，保留合并选项
    experience: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="经验要求")
    degree: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="学历要求")
    salary: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="薪资范围")
    scale: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="公司规模")
    stage: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="融资阶段")
    jobType: MultiSelectConfig = Field(default_factory=MultiSelectConfig, description="工作类型")
    position: List[str] = Field(default_factory=list, description="职位代码")
    industry: List[str] = Field(default_factory=list, description="行业代码")

class AccountConfig(BaseModel):
    username: str = Field(..., description="账户名")
    login_data_file: str = Field("data/account1.json", description="登录数据文件")

class ExcludeKeywordsConfig(BaseModel):
    company_name: List[str] = Field(..., description="公司名称包含以下关键词则排除")
    job_description: List[str] = Field(..., description="职位描述包含以下关键词则排除")

class JobCheckConfig(BaseModel):
    test_mode: bool = Field(..., description="测试模式 (仅投递不活跃HR)")
    salary_range: List[float] = Field(..., description="期望薪资范围 (千元)")
    inactive_status: List[str] = Field(..., description="需要排除的HR不活跃状态")
    check_insurance: bool = Field(..., description="检查社保人数 (未实现)")
    min_insured: int = Field(..., description="最小参保人数 (未实现)")
    exclude_outsource: bool = Field(..., description="排除外包公司 (未实现)")
    check_visited: bool = Field(..., description="检查已投递历史")
    exclude_keywords: Optional[ExcludeKeywordsConfig] = Field(None, description="关键词排除规则")

class EmailConfig(BaseModel):
    enabled: bool = Field(..., description="启用邮件通知")
    smtp_server: str = Field(..., description="SMTP服务器")
    username: str = Field(..., description="邮箱用户名")
    password: str = Field(..., description="邮箱密码/授权码")
    receivers: List[str] = Field(..., description="接收者列表")

class WebhookConfig(BaseModel):
    enabled: bool = Field(..., description="启用Webhook通知")
    url: str = Field(..., description="Webhook URL")

class NotificationConfig(BaseModel):
    email: EmailConfig = Field(..., description="邮件通知")
    webhook: WebhookConfig = Field(..., description="Webhook通知")

class WsClientConfig(BaseModel):
    host: str = Field(..., description="WebSocket主机")
    port: int = Field(..., description="WebSocket端口")

class AppConfig(BaseModel):
    ai: AiConfig = Field(..., description="AI 设置")
    crawler: CrawlerConfig = Field(..., description="爬虫设置")
    application: ApplicationConfig = Field(..., description="投递设置")
    logging: LoggingConfig = Field(..., description="日志设置")
    database: DatabaseConfig = Field(..., description="数据库设置")
    job_search: JobSearchConfig = Field(..., description="职位搜索")
    accounts: List[AccountConfig] = Field(..., description="账户设置")
    job_check: JobCheckConfig = Field(..., description="职位筛选")
    notification: NotificationConfig = Field(..., description="通知设置")
    ws_client: WsClientConfig = Field(..., description="WebSocket设置")

class ConfigManager:
    _instance = None
    config: Optional[AppConfig] = None
    _config_path: str = "config/config.yaml"
    _sample_config_path: str = "config/config_sample.yaml"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load_config(cls, config_path: str = "config/config.yaml"):
        cls._config_path = config_path
        
        if not os.path.exists(config_path):
            print(f"警告: 配置文件 {config_path} 不存在。")
            if os.path.exists(cls._sample_config_path):
                print(f"正在从 {cls._sample_config_path} 创建默认配置文件...")
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                shutil.copy(cls._sample_config_path, config_path)
            else:
                raise FileNotFoundError(f"错误: 配置文件 {config_path} 和模板文件 {cls._sample_config_path} 都不存在。")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        try:
            cls.config = AppConfig(**config_data)
        except ValidationError as e:
            error_messages = [f"{'->'.join(map(str, error['loc']))}: {error['msg']}" for error in e.errors()]
            raise ValueError(f"配置验证错误:\n{os.linesep.join(error_messages)}") from e

    @classmethod
    def get_config(cls) -> AppConfig:
        if cls.config is None:
            cls.load_config()
        return cls.config

    @classmethod
    def get_config_path(cls) -> str:
        return cls._config_path