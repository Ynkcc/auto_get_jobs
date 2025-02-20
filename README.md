# BOSS直聘自动投简历

## 项目简介

**BOSS直投** 是一个自动投简历工具，旨在帮助用户在BOSS直聘平台上更高效地投递简历。该工具提供了自动过滤不活跃的HR、学历、城市、薪资、岗位筛选、AI岗位匹配度分析以及自动打招呼等功能。
## 功能列表

### 已实现功能
- **自动过滤不活跃的HR**
- **学历、城市、薪资、岗位筛选**
- **AI岗位匹配度分析**
- **自动打招呼（BOSS内默认设置）**

### 暂未实现功能
- **定时投稿**
- **AI自动打招呼**

## 注意事项
- 如有能力，请自行确保Chrome浏览器和Chromedriver版本匹配，否则可能导致运行失败。
- 强烈推荐使用miniconda,venv等虚拟环境替代系统环境python
- APIKEY的有效性和余额需要自行管理。
- 仅供学习参考使用，请勿用于非正规用途。
- 大模型开发交流群: [QQ群](https://qm.qq.com/q/oTCtCdWX8A)

## 使用准备

### 大模型APIKEY
- 推荐使用硅基流动平台提供的APIKEY：[硅基流动APIKEY链接](https://cloud.siliconflow.cn/i/u7QBt2Hh)
- 免费配额14元，足够使用几天。
- 硅基平台模型推荐：`Vendor-A/Qwen/Qwen2.5-72B-Instruct`，价格: ¥1/M tokens。

### 前置准备
1. **下载安装最新的Chrome浏览器**
   - [Chrome浏览器下载链接](https://www.google.cn/chrome/)
2. **内置Chromedriver**
   - 无需手动配置，但不能保证100%可用。Chrome和Chromedriver需要版本一致。
   - [Chromedriver下载网址](https://googlechromelabs.github.io/chrome-for-testing)
3. **Python 3.10**
   - [Python 3.10下载链接](https://www.python.org/downloads/)
4. **克隆项目代码**
   ```bash
   git clone https://github.com/SanThousand/auto_get_jobs.git
   ```

## 开始使用

### 1. 安装环境
在项目根目录下运行以下命令，安装所需依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置.env文件
配置`.env`文件，并根据需要配置相关环境变量。

### 3. 配置user_requirements
`user_requirements`文件为简历部分，请格式化写好自己的案例（突出能力和技术栈即可，不要超过70行，工作经验和学历必须填写）。

### 4. 启动main.py
在项目根目录下运行以下命令，启动项目：
```bash
python main.py
```
### 5. 登录BOSS直聘
浏览器会自动打开BOSS直聘，登录即可（60秒内完成登录）。
登录成功后，无需任何操作，等待即可 （可最小化运行）。

## 联系方式
如有任何问题或建议，请联系项目维护者：
- QQ: 1813317076
- GitHub: [SanThousand](https://github.com/SanThousand)
