# test_ai_analyzer.py
import asyncio
import sys
import os
import logging

# --- 步骤1: 设置环境 (已修正) ---
# 显式地将项目根目录（即此脚本所在的目录）添加到Python的模块搜索路径中
# 这是解决 "attempted relative import beyond top-level package" 错误的关键
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 使用从 src 开始的绝对路径导入模块
try:
    from src.common.config_manager import ConfigManager
    from src.services.ai_analyzer import AiAnalyzer
except ImportError as e:
    print(f"错误：无法导入项目模块。请确保此脚本位于项目根目录。")
    print(f"详细信息: {e}")
    sys.exit(1)

# 配置一个简单的日志记录器，方便查看程序内部的输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("AITestScript")


# --- 步骤2: 准备测试数据 ---
# 在这里定义一两个你想测试的职位描述，可以根据你的简历内容进行修改
JOB_DETAIL_PYTHON = """
公司名称：ACME宇宙公司
职位名称：高级Python后端开发工程师
岗位职责：
1. 负责核心业务系统的后端设计、开发和维护；
2. 参与技术方案设计和评审，解决技术难题；
3. 持续优化系统性能、稳定性和可扩展性。
经验要求：3-5年
学历要求：本科
薪资：25-40K
"""

JOB_DETAIL_JAVA = """
公司名称：Cyberdyne系统
职位名称：资深Java开发工程师
岗位职责：
1. 负责大规模分布式系统的设计和开发；
2. 要求精通Java并发编程、JVM调优；
3. 有微服务架构经验，熟悉Spring Cloud生态。
经验要求：5年以上
学历要求：本科
薪资：30-50K
"""

async def main():
    """
    主函数，负责执行所有测试步骤
    """
    logger.info("--- AI 分析器真实调用测试脚本 ---")
    
    analyzer = None
    try:
        # --- 步骤3: 初始化 ---
        logger.info("正在从 'config/config.yaml' 加载配置...")
        ConfigManager.load_config()
        logger.info("配置加载成功。")

        logger.info("正在初始化 AiAnalyzer...")
        analyzer = AiAnalyzer()
        logger.info("AiAnalyzer 初始化完成。")
        logger.info(f"用于分析的简历文件: {analyzer.resume_file_name}")
        logger.info(f"AI 服务提供商: {analyzer.provider}, 模型: {analyzer.model}")
        print("-" * 50)

    except FileNotFoundError:
        logger.error("错误: 'config/config.yaml' 文件未找到。")
        logger.error("请确保在 'config' 目录下已创建并正确配置了该文件。")
        return
    except Exception as e:
        logger.error(f"初始化过程中发生错误: {e}", exc_info=True)
        return

    try:
        # --- 步骤4: 执行测试 ---

        # === 测试点 1: ai_hr_check 方法 ===
        logger.info(">>> 开始测试: ai_hr_check (Python 职位)")
        is_match_py, think_py = await analyzer.ai_hr_check(JOB_DETAIL_PYTHON)
        print("\n--- [结果] ai_hr_check (Python 职位) ---")
        print(f"  是否匹配: {is_match_py}")
        print(f"  AI思考过程: {think_py}")
        print("-" * 50)

        logger.info(">>> 开始测试: ai_hr_check (Java 职位)")
        is_match_java, think_java = await analyzer.ai_hr_check(JOB_DETAIL_JAVA)
        print("\n--- [结果] ai_hr_check (Java 职位) ---")
        print(f"  是否匹配: {is_match_java}")
        print(f"  AI思考过程: {think_java}")
        print("-" * 50)

        # === 测试点 2: ai_greeting 方法 ===
        logger.info(">>> 开始测试: ai_greeting (Python 职位)")
        greeting_py = await analyzer.ai_greeting(JOB_DETAIL_PYTHON)
        print("\n--- [结果] ai_greeting (Python 职位) ---")
        if greeting_py:
            print(f"  生成的打招呼语:\n{greeting_py}")
        else:
            print("  生成打招呼语失败。")
        print("-" * 50)

    except Exception as e:
        logger.error(f"API 调用过程中发生错误: {e}", exc_info=True)

    finally:
        # --- 步骤5: 清理资源 ---
        if analyzer:
            logger.info("正在关闭 AiAnalyzer 会话...")
            await analyzer.close()
            logger.info("会话已关闭。")

if __name__ == "__main__":
    # 检查脚本是否在正确的目录下运行
    if not os.path.exists('src') or not os.path.exists('config'):
        print("错误: 此脚本必须在项目的根目录下运行。")
        print("当前目录:", os.getcwd())
        sys.exit(1)
        
    asyncio.run(main())