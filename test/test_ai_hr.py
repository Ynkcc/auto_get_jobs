import sys
import os
# 将父目录添加到模块搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from utils_async import *
from utils import *
import yaml
import asyncio

config=load_config("config.yaml")
ai=AIAnalyzer(config["ai"])

async def main():
    job_requirements = """职位名称：测试\n岗位职责：1、负责产品软件系统版本管理以及构建、发布和升级； 
2、参与服务器部署、环境搭建、资源调配、系统调优等工作； 
3、负责公司服务器安装、日常巡检、资源监控、网络安全、数据备份等； 4、配合研发部门进行相关软件安装、平台问题分析等技术支持（查数据、跟踪数据、导日志等）工作； 
5、负责远程服务器的日常维护及监控，提供技术支持，保证系统的稳定； 6、负责远程服务器的性能管理和优化，预防问题发生及问题的应急处理，以确保网络系统有持续运作能力。 
7、根据项目具体要求进行软件系统及模块的编码，按计划完成开发目标； 8、协助完成软件系统及模块的需求调研与需求分析； 
9、协助完成软件系统及模块的设计； 
10、协助测试人员完成软件系统及模块的测试； 
11、编制与项目相关的技术文档。
技能说明：
1、熟悉Linux操作系统维护、常用服务的配置、shell脚本编程； 
2、熟悉Linux、Nginx、Redis、Mysql、Mongdodb、ELK、Gitlab-ci/cd、等组件的容器化部署、使用、调优； 
3、有大规模大数据服务集群（包括但不限于Hdfs、Yarn、Hbase、Kafka、Hive、Clickhouse）维护经验； 
4、熟悉hadoop集群hdfs、yarn常见配置文件，熟悉常见参数调整 ； 
5、熟悉基于容器化的微服务持续集成和部署，并能根据开源组件支撑DevOps流程管理代码合并； 
6、熟悉常用业务监控方式，熟练prometheus，granafa等监控工具的使用； 
7、对docker, k8s熟悉, 有3年以上生产环境k8s集群管理和优化经验； 
8、对微服务有相关实践经验，能够熟练使用springboot框架，对springcloud相关组件有一定了解，熟悉常用的数据库比如MySQL，人大金仓等，对常用中间件redis、ActiveMq等有一定场景使用经验，能够高效设计和实现系统后端服务，了解docker和K8s等分布式架构知识，熟悉Linux常用命令，能够基于云平台进行系统问题定位和处理。
    """
    result=await ai.aiHrCheck(job_requirements)
    print(result)

asyncio.run(main())