---
name: wiz-migration
description: 为知笔记数据迁移辅助技能，提供从检测存储目录到完整导出和附件迁移的端到端解决方案
version: 1.0.0
author: OpenClaw Assistant
supported_models: ["*"]
tags: ["migration", "wiz", "笔记", "数据迁移", "文档处理"]
---

# 为知笔记迁移技能

为知笔记数据迁移自动化工具，将复杂的笔记迁移过程转化为标准化、可重复的工作流程。

## 技能使用条件

此技能应在以下情况下使用：

- 从为知笔记迁移数据到其他笔记系统（如Obsidian、Logseq、Notion等）
- 需要批量导出为知笔记中的笔记和附件
- 需要将HTML格式的笔记转换为Markdown格式
- 处理包含大量附件的笔记迁移任务
- 需要自动化重复的迁移操作

## 核心功能概述

执行完整的数据迁移工作流：

1. **检测存储目录** - 自动定位为知笔记数据存储位置
2. **生成导出指南** - 创建详细的操作说明文档
3. **迁移附件文件** - 批量复制所有 _Attachments 和 _files 目录
4. **转换文档格式** - 使用Pandoc将HTML转换为Markdown
5. **修复引用路径** - 自动修复迁移后的附件引用链接

## 资源文件说明

### scripts/ 目录 - 可执行脚本

执行具体的迁移操作：

- `detector.py` - 检测为知笔记数据目录
- `guide_generator.py` - 生成导出操作指南
- `migrator.py` - 主迁移程序，协调各模块工作
- `pandoc_converter.py` - HTML到Markdown转换器
- `add_attachments.py` - 附件管理和路径修复
- `logseq_migrator.py` - Logseq特定迁移逻辑
- `copy_attachments.bat` - Windows批处理附件复制脚本

### references/ 目录 - 参考文档（按需加载）

包含详细的技术文档：

- `wiz_directory_structure.md` - 为知笔记目录结构详解
- `export_requirements.md` - 导出格式要求说明
- `pandoc_usage.md` - Pandoc转换配置和最佳实践
- `attachment_mapping.md` - 附件映射和路径修复逻辑
- `error_solutions.md` - 常见错误解决方案

### templates/ 目录 - 模板文件

提供可重复使用的模板：

- `export_guide_template.md` - 导出指南模板
- `migration_log_template.json` - 迁移日志模板
- `attachment_mapping_template.json` - 附件映射模板

## 迁移工作流执行步骤

### 步骤1：准备导出环境

启动交互式迁移向导：

```python
from wiz_migration import start_wizard
start_wizard()
```

或直接运行主程序：

```bash
python scripts/migrator.py
```

### 步骤2：为知笔记导出操作

指导用户执行正确的为知笔记导出操作：

1. 整理笔记 - 将要迁移的所有内容移动到同一父目录下
2. 执行导出 - 选择要导出的笔记本，右键选择"导出文件" → "导出 HTML"
3. 设置选项 - **必须选择**"导出为多个网页文件（含附件）"，**不要选择**"单个HTML文件"或"渲染Markdown笔记"
4. 选择目标 - 指定导出到空文件夹（建议路径不含空格和特殊字符）

### 步骤3：导出验证

检查导出结果的正确性：

- 确认每个 `.html` 文件旁都有同名的 `_files` 文件夹
- 打开HTML文件验证图片和附件能正常显示
- 检查附件引用路径为相对路径格式（如 `笔记1_files/xxx.png`）

导出后的目录结构应为：

```
导出文件夹/
├── 笔记本1/
│   ├── 笔记1.html
│   ├── 笔记1_files/
│   │   ├── 图片1.png
│   │   └── 附件.pdf
│   └── 笔记2.html
└── 笔记本2/
    ├── 笔记3.html
    └── 笔记3_files/
```

### 步骤4：执行附件迁移

执行附件目录的复制操作：

```python
from wiz_migration import run_attachment_migration

result = run_attachment_migration(
    source_dir="C:/Users/Administrator/Documents/My Knowledge",
    target_dir="G:/Data/knowledge/wiz"
)
```

或直接运行批处理脚本：

```bash
# Windows
scripts/copy_attachments.bat

# Python脚本
python scripts/add_attachments.py <源目录> <目标目录>
```

附件迁移脚本特点：

- 批量复制所有 `_Attachments` 和 `_files` 目录
- 自动跳过已存在的目录，避免重复操作
- 不覆盖现有文件，支持安全重复执行
- 支持Windows、macOS和Linux跨平台运行

### 步骤5：转换文档格式

使用Pandoc将HTML转换为Markdown格式：

```python
from wiz_migration import convert_with_pandoc

result = convert_with_pandoc(
    export_dir="C:/Wiz_Export",      # 为知笔记导出目录
    output_dir="C:/Wiz_Markdown",     # 输出Markdown目录（可选）
    auto_install=True,                # 自动检测并安装Pandoc
    skip_existing=True                # 跳过已存在的Markdown文件
)
```

Pandoc转换功能：

- 自动检测和安装Pandoc（如未安装）
- 批量转换所有HTML文件为Markdown
- 保留原始文档结构和格式
- 支持自定义转换选项和过滤器

### 步骤6：修复附件引用

修复转换后Markdown文件中的附件引用路径：

```python
python scripts/add_attachments.py --fix-refs <markdown目录> <assets目录>
```

此步骤将：

- 查找Markdown文件中的附件引用
- 更新引用路径指向正确的附件位置
- 在文件末尾添加附件链接区域
- 生成附件映射关系文件

## 模块化功能调用

### 独立模块使用

仅使用特定功能模块：

```python
# 1. 检测为知笔记数据目录
from scripts.detector import detect_wiz_data_dir
data_dir = detect_wiz_data_dir()

# 2. 生成导出指南
from scripts.guide_generator import generate_export_guide
guide = generate_export_guide(export_dir="C:/Wiz_Export")

# 3. 附件复制操作
from scripts.add_attachments import migrate_attachments
result = migrate_attachments(source_dir="C:/Users/Admin", target_dir="D:/Wiz")

# 4. 格式转换
from scripts.pandoc_converter import batch_convert_html_to_md
result = batch_convert_html_to_md(input_dir="C:/Wiz_Export", output_dir="C:/Wiz_Markdown")

# 5. Logseq特定迁移
from scripts.logseq_migrator import convert_for_logseq
convert_for_logseq(markdown_dir="C:/Wiz_Markdown", logseq_dir="D:/Logseq")
```

### 完整工作流执行

使用主迁移模块执行完整流程：

```python
from scripts.migrator import migrate_wiz_notes

config = {
    "wiz_data_dir": "C:/Users/Administrator/Documents/My Knowledge",
    "export_dir": "C:/Wiz_Export",
    "output_dir": "D:/Migrated_Notes",
    "convert_to_md": True,
    "fix_attachments": True,
    "target_format": "obsidian"  # obsidian, logseq, notion, generic
}

result = migrate_wiz_notes(config)
```

## 错误诊断和处理

### 常见错误场景

处理迁移过程中可能遇到的错误：

1. **存储目录检测失败**
   - 检查技能目录：`scripts/detector.py`
   - 手动指定路径：`set WIZ_DATA_DIR=你的路径`
   - 验证为知笔记标准安装位置

2. **附件复制权限问题**
   - 以管理员权限运行脚本
   - 检查目标目录写入权限
   - 验证文件系统类型支持

3. **Pandoc转换失败**
   - 自动安装失败时手动安装：https://pandoc.org/installing.html
   - 检查Pandoc版本：`pandoc --version`
   - 调整转换参数或使用备用过滤器

4. **中文编码问题**
   - 确保脚本包含中文编码设置（如`chcp 65001`）
   - 使用UTF-8编码保存所有文件
   - 验证终端/控制台编码支持

5. **路径引用修复失败**
   - 检查附件映射文件生成
   - 验证相对路径计算逻辑
   - 手动修复特定文件的引用

### 故障排除步骤

执行系统化故障排除：

1. **验证环境配置**
   - Python 3.6+环境检查
   - 必要的Python包依赖
   - 系统PATH配置正确性

2. **测试子功能模块**
   ```bash
   python scripts/detector.py --test
   python scripts/add_attachments.py --test
   python scripts/pandoc_converter.py --test
   ```

3. **检查日志和诊断信息**
   - 查看迁移日志文件
   - 分析错误堆栈跟踪
   - 检查中间文件生成

## 最佳实践指南

### 迁移前准备

执行以下准备工作：

1. **数据备份**
   - 完整备份为知笔记`My Knowledge`目录
   - 创建导出前的系统还原点
   - 记录原始目录结构快照

2. **环境验证**
   - 确认Python环境版本兼容性
   - 测试Pandoc安装状态
   - 验证文件系统读写权限

3. **路径规划**
   - 使用不含空格和特殊字符的路径
   - 准备足够的磁盘空间（源数据2-3倍）
   - 规划清晰的目录结构

### 执行过程监控

监控迁移执行过程：

1. **进度跟踪**
   - 启用详细日志输出
   - 定期检查进度状态
   - 监控磁盘使用情况

2. **错误处理**
   - 设置错误中断点
   - 实现错误恢复机制
   - 保留部分成功结果

3. **性能优化**
   - 分批处理大量文件
   - 使用增量迁移方式
   - 优化内存使用策略

### 迁移后验证

验证迁移结果质量：

1. **完整性检查**
   - 验证文件数量一致性
   - 检查附件完整性
   - 确认格式转换准确性

2. **功能性测试**
   - 测试Markdown文件可读性
   - 验证附件链接有效性
   - 检查特殊格式保留情况

3. **性能基准**
   - 记录迁移执行时间
   - 评估资源使用效率
   - 建立性能基线数据

## 技能维护和扩展

### 代码模块结构

理解技能代码组织结构：

```
scripts/
├── detector.py           # 目录检测和路径处理
├── guide_generator.py    # 导出指南生成
├── migrator.py           # 主迁移协调模块
├── pandoc_converter.py   # 格式转换工具
├── add_attachments.py    # 附件管理和路径修复
├── logseq_migrator.py    # Logseq特定适配器
└── copy_attachments.bat  # Windows批处理脚本
```

### 扩展和定制

基于现有技能进行扩展：

1. **添加新格式支持**
   - 实现新的转换适配器
   - 扩展目标格式支持
   - 添加自定义过滤器

2. **增强错误处理**
   - 添加新的错误检测机制
   - 实现更智能的恢复策略
   - 扩展诊断工具集

3. **性能优化**
   - 并行化处理大量文件
   - 实现增量迁移算法
   - 优化内存使用模式

### 测试和验证

建立自动化测试框架：

```bash
# 运行单元测试
python -m pytest tests/

# 执行集成测试
python scripts/migrator.py --test-mode

# 验证迁移结果
python scripts/verifier.py <迁移结果目录>
```

## 技术参考信息

### 为知笔记数据存储结构

参考`references/wiz_directory_structure.md`获取详细的结构说明：

```
My Knowledge/
├── Data/
│   ├── 用户账号1/
│   │   ├── index/         # 笔记索引数据
│   │   ├── attachments/   # 账号特定附件
│   │   └── notes/         # 笔记内容文件
│   └── 用户账号2/
│       └── ...
└── _Attachments/          # 全局共享附件目录
```

### Pandoc转换配置

参考`references/pandoc_usage.md`获取转换选项：

- HTML到Markdown转换参数
- 自定义过滤器和扩展
- 编码和格式处理选项
- 性能优化建议

### 附件映射和路径修复

参考`references/attachment_mapping.md`获取详细逻辑：

- 附件位置检测算法
- 相对路径计算方法
- 引用修复实现细节
- 映射文件格式规范

## 支持和故障排除

### 诊断工具使用

使用内置诊断工具：

```bash
# 系统环境检测
python scripts/detector.py --diagnose

# 附件状态检查
python scripts/add_attachments.py --check <目录>

# 转换配置验证
python scripts/pandoc_converter.py --validate
```

### 获取帮助

遇到问题时执行以下步骤：

1. **收集诊断信息**
   - 运行环境检测工具
   - 收集错误日志文件
   - 记录具体操作步骤

2. **查阅参考文档**
   - 检查`references/`目录中的详细文档
   - 查看常见错误解决方案
   - 参考最佳实践指南

3. **重现和测试**
   - 在测试环境中重现问题
   - 简化问题场景进行调试
   - 逐步验证修复方案
