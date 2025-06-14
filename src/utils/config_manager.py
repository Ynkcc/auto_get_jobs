# config_manager.py
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional
import yaml
import os

class playwrightConfig(BaseModel):
    browser_type: str
    custom_browser_path: str
    headless: bool
    use_default_data_dir: bool

class AiConfig(BaseModel):
    api_url: str
    api_key: str
    model: str
    temperature: float
    provider: str
    resume_for_ai_file: str
    prompt: str
    job_requirements_prompt: str

class CrawlerConfig(BaseModel):
    playwright: playwrightConfig
    rate_limit: Dict[str, float]
    next_page_delay: int
    request_timeout: int
    page_load_timeout: int

class GreetingConfig(BaseModel):
    enable_ai: bool
    greeting_prompt: str

class ApplicationConfig(BaseModel):
    send_resume_image: bool
    resume_image_file: str
    greeting: GreetingConfig
    resume_name: str

class LoggingConfig(BaseModel):
    level: str
    path: str
    max_size: int

class DatabaseConfig(BaseModel):
    filename: str
    export_excel: bool
    excel_path: str

class FilterBaseConfig(BaseModel):
    values: List[str]
    combine: bool

# 新增 CityConfig 模型
class CityConfig(BaseModel):
    values: List[str]
    expand_to_district: bool # 是否展开到地区

class JobSearchConfig(BaseModel):
    city: CityConfig # 修改 city 字段类型
    query: List[str]
    areas: Dict[str, List[str]]
    degree: FilterBaseConfig
    experience: FilterBaseConfig
    position: FilterBaseConfig
    industry: FilterBaseConfig
    salary: List[str]
    jobType: List[str]
    scale: FilterBaseConfig
    stage: FilterBaseConfig

class AccountConfig(BaseModel):
    username: str

class JobCheckConfig(BaseModel):
    test_mode: bool
    salary_range: List[float]
    inactive_status: List[str]
    check_insurance: bool
    min_insured: int
    exclude_outsource: bool
    check_visited: bool

class EmailConfig(BaseModel):
    enabled: bool
    smtp_server: str
    username: str
    password: str
    receivers: List[str]

class WebhookConfig(BaseModel):
    enabled: bool
    url: str

class NotificationConfig(BaseModel):
    email: EmailConfig
    webhook: WebhookConfig

class AppConfig(BaseModel):
    ai: AiConfig
    crawler: CrawlerConfig
    application: ApplicationConfig
    logging: LoggingConfig
    database: DatabaseConfig
    job_search: JobSearchConfig
    accounts: List[AccountConfig]
    job_check: JobCheckConfig
    notification: NotificationConfig

class ConfigManager:
    _instance = None
    config: AppConfig = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load_config(cls, config_path: str = "config/config.yaml"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        try:
            cls.config = AppConfig(**config_data)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                loc = "->".join(str(loc) for loc in error['loc'])
                msg = f"{loc}: {error['msg']}"
                error_messages.append(msg)
            error_messages_str='\n'.join(error_messages)
            raise ValueError(
                f"配置验证错误:\n{error_messages_str}"
            ) from e

    @classmethod
    def get_config(cls) -> AppConfig:
        if cls.config is None:
            raise RuntimeError("配置尚未加载，请先调用load_config方法")
        return cls.config