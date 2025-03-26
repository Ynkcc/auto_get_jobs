import asyncio
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.ai_analyzer import AiAnalyzer
from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

async def debug_ai_greeting():
    config = ConfigManager.get_config()
    ai_analyzer = AiAnalyzer()
    test_job_detail = "职位信息：公司名称：海南信通云服科技\n职位名称：安服工程师\n岗位职责：工作职责：\n1.负责对客户网络、系统、应用进行渗透测试、安全评估和安全加固，编写相关交付报告；\n2.在出现网络攻击或安全事件时，提供应急响应服务，帮助用户恢复系统及调查取证做溯源；\n\n任职要求：\n1.熟悉常见Windows、linux、Web应用和数据库攻击手段；\n2.熟悉Owasp Top10漏洞原理、攻击、防御手法，有渗透测试经验；\n3.具有较好的工作习惯及较强的文档、报告、方案编写能力；\n4.具备优秀的沟通协调能力、学习能力,抗压能力；\n5.具备CISP、cisp-pet等证书优先；\n\n福利待遇：周末双休+法定节假日正常放假+节假日礼品+入职即购买五险一金等；\n经验要求：经验不限\n学历要求：大专"
    greeting = await ai_analyzer.ai_greeting(test_job_detail)
    logger.info(f"AI Greeting: {greeting}")
    print(f"AI Greeting: {greeting}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ConfigManager.load_config("config/config.yaml")
    asyncio.run(debug_ai_greeting())
