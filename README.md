# BOSS直聘自动投简历

## 项目简介
请查看 **[原项目](https://github.com/SanThousand/auto_get_jobs)**

## 补充说明
初次使用，复制项目目录下的config.yaml.sample，重命名为config.yaml后进行修改，其余步骤参考原项目

可以使用以下插件 [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer) 查看保存的数据库`jobs.db`

### 可以做的
- [ ] 添加一个配置文件，替代`user_requirements.md,.env`
- [ ] 使用logger替代print
- [ ] 添加数据库导出excel
- [ ] 规范变量命名，全部改成驼峰命名
- [ ] 识别公司是不是外包，查询社保人数等
- [ ] ai生成招呼语
- [ ] 发送自定义招呼语，发送图片简历（暂时没抓到接口，而且不想用模拟点击的方式完成）
- [ ] 完善openai兼容接口调用的部分
- [ ] 支持多个岗位，多个城市，多个账号（应该和配置文件一块完成）
- [ ] 配置文件包含用户对工作岗位的具体需求，传给ai更多信息
- [ ] 让ai生成搜索关键词
- [ ] 配置文件包含完整的岗位筛选项,如行业，岗位类型，具体到区，或者按区搜索，查询到更多岗位
- [ ] 完善一下文档
- [ ] 使用qt创建一个图形化界面
- [ ] selenium反反爬