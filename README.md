# BOSS直聘自动投简历
> 仅供Python爱好者，交流学习

## 项目简介
boss直聘自动投递，ai根据要求进行筛选

## 使用说明
1. 下载[release](https://github.com/Ynkcc/auto_get_jobs/releases) 中对应系统的压缩包，解压

2. 修改`config`目录下的`config.yaml`

3. 将`resume_for_ai.md`、`resume.png`,改成你的简历文字说明，简历图片

4. 打开控制台,运行 main 程序

 >如果你使用python脚本直接运行。
 >
 >请安装好依赖库后，执行`/src/ws_client/patch.py`

可以使用以下插件 [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer) 查看保存的数据库`jobs.db`

---
计划做一个用户界面，但是涉及大量重构。估计会鸽。

项目内文档部分过时，具体以代码为准

如果你在使用中遇到困难，可以前往交流群 `487194990`寻求帮助

欢迎为本项目做贡献。欢迎PR。佛性维护，欢迎接手。

---

ai模型提供商可以考虑使用azure，学生每年赠送100$。

而且deepseek-r1模型响应也快

---
#### 项目计划

---
**已完成**
- 原项目实现
  - [x] 自动过滤不活跃的HR
  - [x] 学历、城市、薪资、岗位筛选
  - [x] AI岗位匹配度分析
  - [x] 自动打招呼（BOSS内默认设置）
- [x] 使用`config.yaml`作为配置文件
- [x] 岗位搜索参数细分
  - 避免地区岗位过多显示不全
- [x] 使用sqlite数据库保存数据
  - sqlite更轻量,mysql需要额外配置
- [x] 查询数据库数据，避免重复投递
- [x] 用户简历和用户岗位需求独立配置
- [x] AI生成打招呼语，发送自定义招呼语
- [x] 发送图片简历
- [x] 初步实现了MQTT客户端
  - 除发送打招呼语，以及图片简历外，理论可以实现更多功能
- [x] playwright框架替代selenium框架，以优化岗位查询体验
- [x] 从数据库导出excel，pdf生成图片
  - `tests`目录包含脚本
- [x] 完善一下文档
  - 逐步完善中

**计划中** (按优先级排序)
- [ ] 使用qt创建一个图形化界面
- [ ] 优化一下导出的excel的格式
- [ ] 使用重试队列，解决MQTT客户端会漏消息的问题
- [ ] 支持pdf发送简历
  - 即自动将pdf转成图片后再发送
- [ ] 对于同一公司的相似岗位，不重复投递
- [ ] 响应hr简历请求
- [ ] 将现有的工作详情查询和岗位沟通的接口操作改成playwright的模拟操作
- [ ] 令牌桶管理所有与boss直聘通信的http请求
  - 把请求塞到playwright里，然后通过playwright提供的route方法拿令牌桶限速
- [ ] 到达投递上限后自动切号
- [ ] 让ai生成搜索关键词，扩展可接受岗位
- [ ] 数据库数据共享
- [ ] 识别公司是不是外包，查询社保人数等
---

## LICENSE
[GNU General Public License v3.0](./LICENSE)

---

### 其他同类项目
- [yangfeng20/boss_batch_push](https://github.com/yangfeng20/boss_batch_push) 油猴脚本
- [loks666/get_jobs](https://github.com/loks666/get_jobs) Java项目，多平台
- [lastsunday/job-hunting](https://github.com/lastsunday/job-hunting) 浏览器插件，多平台
- [Ocyss/boos-helper](https://github.com/Ocyss/boos-helper) 浏览器插件
- [IceyOrange/AutoBOSS](https://github.com/IceyOrange/AutoBOSS)  Python项目 
- [rebibabo/Job-Hunting-Agent](https://github.com/rebibabo/Job-Hunting-Agent) Python项目

本项目fork自 [SanThousand/auto_get_jobs](https://github.com/SanThousand/auto_get_jobs)

---

### 更新日志

##### [v0.6.0]
- 使用`src/ws_client/patch.py`对paho-mqtt库进行修改
- 添加测试模式，不考虑薪资范围，仅投递不活跃的hr
- 使用使用nuitka打包成可执行文件直接运行，添加actions实现自动打包
- 运行正常结束后，导出sqlite数据库为excel文件

##### [v0.5.0](https://github.com/Ynkcc/auto_get_jobs/commit/e226aa759c755c8f4ca2d45b672c58c7ebcc8a2a)
- 使用playwright框架替代selenium框架
  - selenium框架会触发boss的安全检查跳转，playwright则不会
- 支持匹配薪资上限
- 支持控制是否过滤已访问工作岗位
- 添加了独立的岗位需要提示词配置项
- 数据库添加首次保存岗位的时间记录，添加思考模型的思考内容记录
- 优化了生成打招呼语的默认提示词，支持自定义打招呼语生成的提示词
- 缩短了mqtt-client的心跳时间，缓解了漏消息的问题
- readme添加了更新日志

##### [v0.4.0](https://github.com/Ynkcc/auto_get_jobs/commit/293d243987c08274a45d4fd9c901b3911f9a70c2)
- 支持发送图片简历
- ai生成自定义打招呼语
- 岗位搜索支持特定项，进行参数合并

##### [v0.3.0](https://github.com/Ynkcc/auto_get_jobs/commit/096d34148b5942bc47d2286e2f64f51497fb68a8)
- 实现了mqtt-client
- 添加ConfigManager，用于处理配置文件的解析与传递
- 添加SessionManager,用于管理cookies更新，以及同步以及异步session的复用
- 添加了logger，替代print作为日志输出，同时将日志输出到文件

##### [v0.2.0](https://github.com/Ynkcc/auto_get_jobs/commit/789c2c34cb310f46b1eb38fe1b15c6820eb83203)
- 使用`github action`将代码同步到gitee
- 规范整理了目录结构
- readme添加了其他同类项目，以及todo
- 添加了yaml配置文件
- 添加了对edge的支持，添加了webdriver配置的相关文档
- 支持webdriver使用用户默认配置文件
- 修改了岗位搜索链接的构造函数，对搜索岗位进行细分
  缓解大城市岗位过多，查询结果只能显示10页岗位不全的问题
- 不再使用azure sdk，而是通过api接口直接调用
- 添加了openai兼容接口的ai配置
- 添加了GPL-3.0 license

##### [v0.1.0](https://github.com/Ynkcc/auto_get_jobs/commit/37ee841b95af80d87eb41b1bf19d4ebb8e0095ec)
- 添加了数据库支持，过滤已访问岗位
- 薪资过滤的部分从原本的ai调用上剥离出来
  - 原作者实现是根据岗位名称以及薪资，进行一次预判断
- 使用azure sdk进行ai调用
  - 因为那段时间，azure deepseek-r1调用免费
- 使用令牌桶进行限速