# src/common/config_manager.py
from pydantic import BaseModel, ValidationError, Field
from typing import Dict, Any, List, Optional
import yaml
import os
import shutil

class PlaywrightConfig(BaseModel):
    browser_type: str
    custom_browser_path: str
    headless: bool
    use_default_data_dir: bool
    scroll_pages: int = 3

# 修改点4: 新增AI Provider模型
class AiProvider(BaseModel):
    id: str
    name: str
    api_url: str
    api_key: str
    model: str
    temperature: float
    provider: str
    api_version: Optional[str] = None

# 修改点4: 修改AIConfig模型
class AiConfig(BaseModel):
    active_ai_id: str
    providers: List[AiProvider]
    prompt: str
    job_requirements_prompt: str
    resume_for_ai_file: str

class CrawlerConfig(BaseModel):
    playwright: PlaywrightConfig
    rate_limit: Dict[str, float]
    next_page_delay: int
    request_timeout: int
    page_load_timeout: int

class GreetingConfig(BaseModel):
    enable_ai: bool
    greeting_prompt: str
    greeting_for_ai_file: str # 新增未实现字段

class ApplicationConfig(BaseModel):
    send_resume_image: bool
    resume_image_file: str
    greeting: GreetingConfig
    resume_name: str # 新增未实现字段

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

class CityConfig(BaseModel):
    values: List[str]
    expand_to_district: bool

class JobSearchConfig(BaseModel):
    city: CityConfig
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
    login_data_file: str = "data/account1.json"

class ExcludeKeywordsConfig(BaseModel):
    company_name: List[str]
    job_description: List[str]

class JobCheckConfig(BaseModel):
    test_mode: bool
    salary_range: List[float]
    inactive_status: List[str]
    check_insurance: bool
    min_insured: int
    exclude_outsource: bool
    check_visited: bool
    exclude_keywords: Optional[ExcludeKeywordsConfig] = None

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

class WsClientConfig(BaseModel):
    host: str
    port: int

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
    ws_client: WsClientConfig
    
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