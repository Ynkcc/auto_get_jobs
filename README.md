# BOSS直聘自动投简历
> 仅供Python爱好者，交流学习

### 其他同类项目
- [yangfeng20/boss_batch_push](https://github.com/yangfeng20/boss_batch_push) 油猴脚本
- [loks666/get_jobs](https://github.com/loks666/get_jobs) Java项目，多平台
- [lastsunday/job-hunting](https://github.com/lastsunday/job-hunting) 浏览器插件，多平台
- [Ocyss/boos-helper](https://github.com/Ocyss/boos-helper) 浏览器插件
- [IceyOrange/AutoBOSS](https://github.com/IceyOrange/AutoBOSS)  Python项目 
- [Frrrrrrrrank/auto_job__find__chatgpt__rpa](https://github.com/Frrrrrrrrank/auto_job__find__chatgpt__rpa) Python项目

本项目fork自 [SanThousand/auto_get_jobs](https://github.com/SanThousand/auto_get_jobs)
## 项目简介
> 请查看 **[原项目](https://github.com/SanThousand/auto_get_jobs)**

## 使用说明
详细教程请点击 [详细部署教程](docs/部署指南.md)  
初次使用，复制`data`目录下的`config.yaml.sample`，重命名为`config.yaml`后进行修改，其余步骤参考原项目

可以使用以下插件 [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer) 查看保存的数据库`jobs.db`

---
目前仍在开发，部分功能可能不可用

如果你在使用过程中遇到bug，请提交反馈

如果你喜欢PYTHON，且愿意为本项目做贡献。欢迎PR

交流群 `487194990`

---
#### 项目计划
- [ ] 使用logger替代print
- [ ] 从数据库导出excel
- [ ] 规范变量命名，全部改成下划线命名格式
- [ ] 识别公司是不是外包，查询社保人数等
- [ ] ai生成招呼语
- [ ] 发送自定义招呼语，发送图片简历（暂时没抓到接口，而且不想用模拟点击的方式完成）
- [ ] 配置文件包含用户对工作岗位的具体需求，传给ai更多信息
- [ ] 让ai生成搜索关键词
- [ ] 完善一下文档
- [ ] 使用qt创建一个图形化界面
- [ ] selenium反反爬
- [ ] 到达投递上限后自动切号

## LICENSE
[GNU General Public License v3.0](./LICENSE)