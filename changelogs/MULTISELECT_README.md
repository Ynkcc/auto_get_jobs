# 多选下拉框功能实现说明

## 功能概述

本次更新为BOSS直聘自动投简历项目实现了多选下拉框功能，用户可以在配置界面中选择多个搜索条件，同时保留了"是否合并为单次请求"的配置选项。

## 主要特性

### 1. 多选下拉框组件
- **MultiSelectComboBox**: 基础多选下拉框，支持多个选项的选择
- **MultiSelectWithCombineWidget**: 带合并选项的多选组件，包含合并复选框

### 2. 配置模型更新
- **MultiSelectConfig**: 新的配置模型，包含`values`（选中值列表）和`combine`（是否合并）字段
- 支持的多选字段：`experience`、`degree`、`salary`、`scale`、`stage`、`jobType`

### 3. URL构建逻辑
- 自动处理多选配置，根据`combine`选项决定是否合并参数
- `combine=True`: 参数合并为逗号分隔的字符串 (如: `experience=104,105,106`)
- `combine=False`: 参数分别生成多个URL组合

### 4. 配置文件迁移
- 提供`migrate_config.py`工具自动迁移现有配置文件
- 支持从旧格式平滑升级到新格式

## 文件结构

```
src/
├── gui/
│   ├── widgets.py              # 新增：多选组件
│   └── config_window.py        # 更新：支持多选组件
├── common/
│   ├── config_manager.py       # 更新：新增MultiSelectConfig
│   └── file_utils.py           # 更新：处理多选URL构建
migrate_config.py               # 新增：配置迁移工具
test_multiselect.py            # 新增：功能测试脚本
demo_multiselect.py            # 新增：功能演示脚本
```

## 使用方法

### 1. 迁移现有配置
```bash
python migrate_config.py
```

### 2. 启动GUI界面
```bash
python -m src.gui.main_window
```

### 3. 配置多选选项
1. 在GUI中点击"职位搜索"标签页
2. 找到需要配置的多选字段（如"经验要求"）
3. 点击多选按钮选择多个选项
4. 设置"合并为单次请求"选项
5. 保存配置

## 配置格式示例

### 新格式（推荐）
```yaml
job_search:
  experience:
    values: [104, 105, 106]  # 1-3年, 3-5年, 5-10年
    combine: true            # 合并为单次请求
  degree:
    values: [203, 204]       # 本科, 硕士
    combine: false           # 分别生成请求
```

### 参数映射
```json
{
  "experience": {
    "不限": 0,
    "在校生": 108,
    "应届生": 102,
    "经验不限": 101,
    "1年以内": 103,
    "1-3年": 104,
    "3-5年": 105,
    "5-10年": 106,
    "10年以上": 107
  }
}
```

## 技术实现

### 1. 组件架构
- **MultiSelectComboBox**: 基础多选功能
- **MultiSelectWithCombineWidget**: 组合多选和合并选项
- **ConfigWindow**: 集成多选组件到配置界面

### 2. 数据流程
1. 用户在GUI中选择多个选项
2. 组件更新配置模型中的`values`和`combine`字段
3. 保存配置时验证并写入YAML文件
4. URL构建时根据配置生成相应的搜索URL

### 3. 兼容性
- 完全兼容现有配置文件格式
- 提供自动迁移工具
- 向后兼容旧版本配置

## 测试验证

### 运行测试
```bash
python test_multiselect.py
```

### 功能演示
```bash
python demo_multiselect.py
```

## 预期效果

### URL生成示例
配置：`experience: {values: [104, 105], combine: true}`

生成URL：
```
https://www.zhipin.com/web/geek/job?city=101310100&experience=104,105&query=Python
```

配置：`experience: {values: [104, 105], combine: false}`

生成URL：
```
https://www.zhipin.com/web/geek/job?city=101310100&experience=104&query=Python
https://www.zhipin.com/web/geek/job?city=101310100&experience=105&query=Python
```

## 注意事项

1. **配置迁移**: 首次使用前请运行迁移工具
2. **备份**: 迁移工具会自动备份原配置文件
3. **验证**: 迁移后请验证配置是否正确
4. **性能**: 关闭合并选项会增加URL数量，可能影响搜索性能

## 相关依赖

- PySide6: GUI界面
- qfluentwidgets: 现代化UI组件
- pydantic: 数据验证和序列化
- PyYAML: 配置文件处理

## 总结

本次实现成功为项目添加了多选下拉框功能，在保持配置简洁的同时，大大提升了用户体验和配置灵活性。用户可以更精确地控制搜索条件，同时保留了对请求合并的细粒度控制。
