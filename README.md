# 为知笔记迁移技能

为知笔记数据迁移工具，提供完整的自动化迁移流程。

## 核心功能

- 🔍 **智能检测** - 自动定位为知笔记数据目录
- 📝 **导出指南** - 生成详细的HTML导出操作说明
- 📎 **附件迁移** - 批量复制所有附件文件
- 🔄 **格式转换** - 使用Pandoc将HTML批量转换为Markdown
- 🔧 **路径修复** - 自动修复附件引用路径
- 🖥️ **跨平台支持** - Windows / macOS / Linux

## 快速开始

### 1. 启动迁移向导

```bash
# 启动交互式向导
python -m wiz_migration

# 或使用入口文件
python bin/wiz-migrate
```

### 2. 按照向导步骤操作

向导将引导完成完整迁移流程：
1. 检测为知笔记数据目录
2. 生成导出指南（保存为 `wiz_export_guide.md`）
3. 迁移附件文件
4. 转换HTML到Markdown格式
5. 修复附件引用路径
6. 完成检查和验证

## 主要模块

### 核心脚本

```
scripts/
├── detector.py           # 数据目录检测
├── guide_generator.py    # 导出指南生成
├── migrator.py           # 主迁移逻辑
├── pandoc_converter.py   # HTML → Markdown 转换
├── add_attachments.py    # 附件管理和路径修复
└── copy_attachments.bat  # Windows批处理脚本
```

### 参考文档

详细技术文档见 `references/` 目录：
- `wiz_directory_structure.md` - 为知笔记目录结构详解
- `export_requirements.md` - 导出格式要求说明
- `pandoc_usage.md` - Pandoc转换配置和最佳实践

## API使用方法

### 完整工作流

```python
from wiz_migration import start_wizard
start_wizard()
```

### 独立功能模块

```python
# 检测数据目录
from wiz_migration import detect_wiz_data_dir
data_dir = detect_wiz_data_dir()

# 生成导出指南
from wiz_migration import generate_export_guide
guide_path = generate_export_guide("C:/Wiz_Export")

# 迁移附件
from wiz_migration import run_attachment_migration
result = run_attachment_migration("C:/源目录", "D:/目标目录")

# 格式转换
from wiz_migration import convert_with_pandoc
result = convert_with_pandoc("C:/Wiz_Export", "C:/Wiz_Markdown")
```

## 系统要求

- Python 3.6+
- 操作系统：Windows / Linux / macOS
- 为知笔记客户端（用于导出）
- 足够的磁盘空间

## 注意事项

1. **备份原始数据** - 迁移前务必备份为知笔记数据
2. **导出格式** - 必须选择"多个网页文件（含附件）"格式
3. **路径安全** - 避免路径包含特殊字符或空格
4. **权限要求** - 需要读取源目录、写入目标目录的权限
5. **增量复制** - 脚本自动跳过已存在文件，可安全重复运行

## 技术支持

如有问题，请检查：
- 是否为知笔记导出格式正确
- 是否有足够的文件读写权限
- 路径是否正确

## 许可证

MIT

---

**注意**：本技能仅作为迁移辅助工具，请务必保留原始数据备份。