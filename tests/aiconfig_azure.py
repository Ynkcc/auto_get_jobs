import os
import json
import time
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import re


# 加载环境变量
load_dotenv()

# 配置 Azure API 端点和密钥
endpoint = os.getenv("AZUREAI_ENDPOINT_URL").strip()
key = os.getenv("AZUREAI_ENDPOINT_KEY").strip()
model = os.getenv("MODEL").strip()

# 创建 Azure 客户端
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

# 检测匹配度用的
def ai_response(content):
    messages = [
        {"role": "user", "content": content}
    ]
    data = {
        'model': model,
        'temperature': 0.2,
        #'max_tokens': 100,
        'messages': messages
    }
    for _ in range(5):
        try:
            response = client.complete(
                messages=messages,
                model=model,
                temperature=0.2,
                #max_tokens=100
            )
            story = response.choices[0].message.content
            return story
        except Exception as e:
            print(f"请求错误，正在重试... 错误原因: {e}")
            time.sleep(1)
    return None

# 模拟HR判断岗位是否合适。
def ai_hr(job_requirements, user_requirements, first_response=None, data_analysis=False):
    hr_prompt = """
    # Role: 经验丰富的HR\n
    \n
    ## Profile\n
    - author: suancaiyv\n
    - version: 1.0\n
    - language: 中文\n
    - description: 经验丰富的HR主管，根据公司发布的招聘需求和应聘者的简历信息，精准判断应聘者是否与岗位匹配，具备精准筛选判断能力。\n
    \n
    ## Goals\n
    1. 精准评估应聘者的简历内容，并根据公司发布的岗位要求进行匹配度分析。\n
    2. 基于简历和岗位描述的匹配情况，提供清晰的筛选建议。\n
    \n
    ## Skills\n
    1. 熟悉关键岗位的要求，能够准确提炼职位的关键技能和素质要求。\n
    2. 具备丰富的简历筛选与应聘者评估经验，能够从简历中识别核心技能和潜力。\n
    3. 准确判断应聘者与岗位的匹配度，依据岗位需求与应聘者简历中关键要素的对比。\n
    4. 有效沟通能力，能提供关于匹配结果的清晰判断依据。\n
    \n
    ## Rules\n
    1. 充分阅读并理解公司提供的招聘需求，包括工作经验、职位职责、所需技能、经验要求及软性条件。\n
    2. 仔细审阅应聘者的简历，重点关注其技能、工作经历、成就以及其他与职位要求相关的特质。\n
    3. 如果应聘者的背景与岗位要求存在显著差异，应以清晰的理由进行说明。\n
    4. 根据匹配度对候选人进行分类，提供推荐等级，并提供简洁的理由。\n
    \n
    ## OutputFormat:\n
    1. 输出推荐指数。\n
    2. 输出你给这个推荐指数以及理由（200字即可）。\n
    3. 缺少的技术栈。\n
    4. 除了以上内容不要输出多余内容。\n
    """
    
    # 设置对话的消息
    messages = [
        {"role": "system", "content": hr_prompt},
        {"role": "assistant", "content": "我已理解您的需求，请告诉我公司岗位要求以及应聘者的基本信息。"},
        {"role": "user", "content": f"以下是公司的招聘岗位要求，如果你理解岗位要求，回复“理解即可”。\n 招聘岗位要求：{job_requirements}"},
        {"role": "assistant", "content": "理解"},
        {"role": "user", "content": f"以下是应聘者的基本简历，阅读并理解基本简历遵循[workflow]流程开始工作。\n 应聘者基本简历：{user_requirements}"}
    ]
    
    if first_response:
        messages.append({"role": "assistant", "content": first_response})
    
    if data_analysis:
        messages.append({"role": "user", "content": "结合以上信息和分析结果，精准判断应聘者是否与岗位匹配，如果匹配值大于“0.5”则返回“true”，匹配值小于“0.5”则返回“false”，不要对以上内容进行讨论和输出任何多余内容，只输出true或false即可。"})
    
    # 调用 Azure AI API
    data = {
        'model': model,
        'temperature': 0.2,
        #'max_tokens': 1024,
        'messages': messages
    }
    
    for _ in range(5):
        try:
            response = client.complete(
                messages=messages,
                model=model,
                temperature=0.2,
                #max_tokens=1024
            )

            # print("Model:", response.model)
            # print("Usage:")
            # print("\tPrompt tokens:", response.usage.prompt_tokens)
            # print("\tTotal tokens:", response.usage.total_tokens)
            # print("\tCompletion tokens:", response.usage.completion_tokens)

            match = re.match(r"<think>(.*?)</think>(.*)", response.choices[0].message.content, re.DOTALL)

            # print("Response:", )
            if match:
                # print("\tThinking:", match.group(1))
                # print("\tAnswer:", match.group(2))
                return match.group(2)
            else:
                print("\tAnswer:", response.choices[0].message.content)

            return response.choices[0].message.content
        
        except Exception as e:
            print(f"请求错误，正在重试... 错误原因: {e}")
            time.sleep(1)
    
    return None


if __name__ == "__main__":
    # 示例调用
    # URL = "https://api.siliconflow.cn/v1/chat/completions"  # OpenAI API的实际端点
    # KEY = "" # 替换为您的实际API密钥
    # MODEL = "Vendor-A/Qwen/Qwen2.5-72B-Instruct"  # 使用的模型

    job_requirements = """
    岗位名称：Python开发工程师

    岗位职责：
    1. 负责公司后台系统的开发和维护；
    2. 参与系统架构设计，优化系统性能；
    3. 编写相关的技术文档。

    任职要求：
    1. 计算机相关专业本科及以上学历；
    2. 熟练掌握Python，熟悉Django或Flask框架；
    3. 有至少2年以上的Python开发经验；
    4. 熟悉数据库设计与优化，掌握MySQL或PostgreSQL；
    5. 良好的团队合作精神和沟通能力。
    """

    user_requirements = """
    姓名：张三
    学历：本科，市场营销专业
    工作经验：
    1. 在ABC公司担任Java开发工程师1年，主要负责Web应用的开发，使用Spring框架；
    2. 熟悉Oracle数据库，参与过数据库设计和优化项目；
    3. 有良好的团队协作经验，参与过多个跨部门项目的开发。

    技能：
    - 熟悉Java编程；
    - 了解Spring框架；
    - 掌握Oracle数据库；
    - 了解前端技术，如HTML、CSS、JavaScript。

    自我评价：
    热爱技术，学习能力强，善于解决复杂问题，具有良好的沟通和协作能力。
    """

    # 初步分析
    first_response = ai_hr(job_requirements, user_requirements)
    #print("初步分析结果:", first_response)

    # # 最终分析
    final_analysis = ai_hr(job_requirements, user_requirements, first_response, data_analysis=True)
    print("最终分析结果:", final_analysis)
    