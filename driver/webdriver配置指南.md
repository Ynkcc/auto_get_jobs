# WebDriver 配置指南

本指南将帮助您根据选择的浏览器类型（Chrome/Edge）配置对应的浏览器驱动。


## 浏览器类型选择

在项目配置文件 `config.yaml` 中指定使用的浏览器类型：

```yaml
crawler:
  webdriver:
    browser_type: "chrome"  # 可选值：chrome / edge
```

## 查看浏览器版本

### Chrome 浏览器

- 点击右上角 ⋮ 菜单
- 选择 帮助 > 关于 Google Chrome


### Edge 浏览器

- 点击右上角 ... 菜单
- 选择 帮助和反馈 > 关于 Microsoft Edge


## 下载浏览器驱动

### Chrome 驱动

- 访问 [ChromeDriver 官方下载页](https://googlechromelabs.github.io/chrome-for-testing)
- 选择与浏览器版本匹配的驱动版本（主版本号必须一致）
- 下载对应操作系统的驱动包

### Edge 驱动

- 访问 [EdgeDriver 官方下载页](https://developer.microsoft.com/zh-cn/microsoft-edge/tools/webdriver)
- 选择与浏览器版本匹配的驱动版本
- 下载对应操作系统的驱动包

## 驱动存放路径

在项目根目录创建 `driver` 文件夹，解压下载的驱动文件，按以下名称存放：

```
this_project/
├── driver/
│   ├── chromedriver.exe   # Chrome 驱动
│   └── msedgedriver.exe   # Edge 驱动
```

## 配置示例

```yaml
crawler:
  webdriver:
    browser_type: "edge"  # 浏览器类型
    edge_driver_path: "driver/msedgedriver.exe"  # Edge驱动路径
    chrome_driver_path: "driver/chromedriver.exe"  # Chrome驱动路径
    headless: false
```

## 常见问题

### 驱动版本不匹配

**现象：** SessionNotCreatedException 错误

**解决：** 确保浏览器版本与驱动版本完全一致

### 驱动文件路径错误

**现象：** WebDriverException: Message: 'xxx' executable needs to be in PATH

**解决：**

- 检查配置文件中的路径是否正确
- 确认驱动文件已放入指定目录