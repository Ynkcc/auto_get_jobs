# app_core/utils/logging_config.py
import logging
import logging.config
import os
import sys
from datetime import datetime

def setup_logging(log_config: dict):
    """
    根据提供的配置字典设置日志。
    :param log_config: 日志配置字典，通常来自 config.yaml 中的 'log' 部分。
    """
    # 确保日志目录存在
    log_dir = log_config.get("log_dir", "logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            # 处理并发创建目录时可能发生的错误
            if not os.path.exists(log_dir):
                print(f"错误:无法创建日志目录 {log_dir}. {e}", file=sys.stderr)
                return # 如果无法创建日志目录，则不继续配置基于文件的日志记录器

    # 为文件名添加日期和时间戳，避免覆盖
    # 例如：app_2023-10-27_15-30-00.log
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 使用固定的文件名或配置中的文件名，由 logrotate 等外部工具处理日志轮换
    # 如果要使用时间戳文件名，取消注释上面的行，并修改下面的文件名模板

    # 构建日志配置文件字典 (Python logging format)
    # 我们将从传入的 log_config 构建它
    
    # 默认配置
    default_logging_config = {
        "version": 1,
        "disable_existing_loggers": False, # 不禁用已存在的记录器
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_config.get("console_level", "INFO").upper(), # 控制台日志级别
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file_handler": {
                "class": "logging.handlers.RotatingFileHandler", # 或者 TimedRotatingFileHandler
                "level": log_config.get("file_level", "DEBUG").upper(), # 文件日志级别
                "formatter": "standard",
                "filename": os.path.join(log_dir, log_config.get("log_filename", "app.log")),
                "maxBytes": log_config.get("log_max_bytes", 1024 * 1024 * 10),  # 默认10MB
                "backupCount": log_config.get("log_backup_count", 5), # 保留5个备份
                "encoding": "utf-8",
            },
        },
        "root": { # 根记录器配置
            "level": log_config.get("root_level", "DEBUG").upper(), # 根记录器的最低级别
            "handlers": ["console", "file_handler"],
        },
        "loggers": { # 特定记录器的配置 (可以覆盖根记录器)
            # 例如，减少某些库的日志级别
            "sqlalchemy.engine": {
                "level": log_config.get("sqlalchemy_level", "INFO").upper(),
                "handlers": ["console", "file_handler"],
                "propagate": False, # 不传递给根记录器
            },
            "websockets": { # 如果使用了websockets库
                "level": log_config.get("websockets_level", "INFO").upper(),
                "handlers": ["console", "file_handler"],
                "propagate": False,
            },
            "playwright": {
                 "level": log_config.get("playwright_level", "WARNING").upper(),
                 "handlers": ["console", "file_handler"],
                 "propagate": False,
            }
            # 可以在这里为 app_core.services.crawler_service 等模块单独配置
            # "app_core.services.crawler_service": {
            #     "level": "DEBUG",
            #     "handlers": ["file_handler"], # 只写入文件
            #     "propagate": False
            # }
        }
    }
    
    try:
        logging.config.dictConfig(default_logging_config)
        logging.info("日志系统已根据配置初始化。")
        # print(f"日志配置成功。控制台级别: {log_config.get('console_level', 'INFO')}, 文件级别: {log_config.get('file_level', 'DEBUG')}")
    except Exception as e:
        # 如果日志配置失败，打印到stderr并使用基本配置
        print(f"错误: 日志配置失败. {e}", file=sys.stderr)
        logging.basicConfig(level=logging.INFO)
        logging.error("日志配置失败，已回退到基本配置。", exc_info=True)

if __name__ == '__main__':
    # 测试日志配置
    sample_log_config_from_yaml = {
        "log_dir": "test_logs",
        "log_filename": "test_app.log",
        "console_level": "INFO",
        "file_level": "DEBUG",
        "root_level": "DEBUG",
        "sqlalchemy_level": "WARNING"
        # "log_max_bytes": 1024, # for quick rotation test
        # "log_backup_count": 2
    }
    setup_logging(sample_log_config_from_yaml)

    # 获取不同模块的logger进行测试
    root_logger = logging.getLogger()
    app_logger = logging.getLogger("app_core.main_logic") # 假设的模块
    db_logger = logging.getLogger("sqlalchemy.engine")

    root_logger.debug("这是一条来自根记录器的DEBUG信息。")
    root_logger.info("这是一条来自根记录器的INFO信息。")
    app_logger.debug("这是一条来自应用逻辑的DEBUG信息。")
    app_logger.info("这是一条来自应用逻辑的INFO信息。")
    app_logger.error("这是一条来自应用逻辑的ERROR信息。")
    db_logger.info("这是一条来自SQLAlchemy的INFO信息（应该看不到，因为我们设了WARNING）。") # 不会显示
    db_logger.warning("这是一条来自SQLAlchemy的WARNING信息。")

    print(f"测试日志已生成到 '{sample_log_config_from_yaml['log_dir']}' 目录。")
