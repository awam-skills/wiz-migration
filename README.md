# 为知笔记迁移技能 (Wiz Migration)

> 版本: 1.0.0 | 作者: OpenClaw Assistant

为知笔记数据迁移辅助工具，提供自动化检测、交互式引导和一键迁移功能。

## 快速使用

```bash
# 启动交互式向导
python -m wiz_migration

# 或使用入口文件
python bin/wiz-migrate
```

## 功能特点

- 🔍 **智能检测**：自动查找为知笔记数据目录
- 📝 **导出指南**：生成详细的 HTML 导出操作指南
- 📎 **附件迁移**：批量复制所有附件文件
- 🔄 **Pandoc 转换**：自动安装 Pandoc，批量转换 HTML → Markdown
- 🖥️ **跨平台**：支持 Windows/macOS/Linux
- ⚡ **增量复制**：自动跳过已存在的文件

## 主要功能

### 1. 自动检测数据目录

自动识别标准安装路径：
- `C:\Users\Administrator\Documents\My Knowledge\Data`
- `$HOME/Documents/My Knowledge/Data`

如果自动检测失败，支持手动输入路径。

### 2. 生成导出指南

在 `wiz_export_guide.md` 中生成：
- 为知笔记导出的详细步骤
- 关键选项说明（避免常见错误）
- 目录结构示例
- 导出后检查清单

**关键提醒：**
- ✅ 必须选择"导出为多个网页文件（含附件）"
- ❌ 不要选择"单个 HTML 文件"（附件会被内嵌）
- ❌ 不要勾选"渲染 Markdown 笔记"（会丢失结构）

### 3. 附件批量迁移

自动复制所有 `_Attachments` 目录：
- 已存在自动跳过
- 可重复执行，不覆盖
- 提供详细进度和统计

同时提供 Windows 批处理脚本 `copy_attachments.bat` 供独立使用。

### 4. Pandoc 自动安装与转换

**自动安装 Pandoc**（支持 Windows/macOS/Linux）：
- Windows：winget / chocolatey / scoop
- macOS：Homebrew / MacPorts
- Linux：apt / dnf / yum / pacman

**批量转换 HTML → Markdown**：
- 自动检测 Pandoc，未安装则尝试自动安装
- 递归扫描所有子目录的 HTML 文件
- 保留附件引用（_files 目录）
- 跳过已存在的 Markdown 文件（可重复运行）

### 5. 交互式向导

`start_wizard()` 提供完整的一步一步迁移流程：
1. 检测数据目录
2. 生成导出指南
3. 迁移附件
4. 完成检查和后续建议

## API 使用方法

```python
from wiz_migration import (
    detect_wiz_data_dir,
    generate_export_guide,
    run_attachment_migration,
    convert_with_pandoc,
    interactive_convert,
    start_wizard
)

# 检测数据目录
data_dir = detect_wiz_data_dir()

# 生成导出指南
guide_path = generate_export_guide(
    export_dir="C:/Wiz_Export",
    output_file="export_guide.md"
)

# 迁移附件
result = run_attachment_migration(
    source_dir="C:/Users/Admin/Documents/My Knowledge",
    target_dir="G:/Data/wiz"
)

# 一键转换 HTML → Markdown（自动安装 Pandoc）
result = convert_with_pandoc(
    export_dir="C:/Wiz_Export",  # 为知笔记导出目录
    output_dir="C:/Wiz_Markdown",  # 输出目录（可选，默认同源目录）
    auto_install=True,  # 自动安装 Pandoc
    skip_existing=True  # 跳过已存在的 MD 文件
)

# 交互式转换向导
interactive_convert()

# 完整向导
start_wizard()
```

## 目录结构

```
wiz-migration/
├── SKILL.md              # 技能说明文档
├── README.md             # 本文件
├── __init__.py           # 包入口
├── bin/
│   ├── wiz-migrate       # 可执行入口（主程序）
│   └── __init__.py
├── scripts/
│   ├── detector.py       # 数据目录检测
│   ├── guide_generator.py  # 导出指南生成
│   ├── migrator.py       # 附件迁移逻辑
│   ├── copy_attachments.bat # Windows 批处理脚本
│   └── __init__.py
└── templates/
    └── (动态生成的模板文件)
```

## 为知笔记数据目录结构

```
My Knowledge/
├── Data/
│   ├── 账号1/
│   │   ├── index/       # 笔记索引
│   │   └── attachments/ # 账号附件
│   └── 账号2/
└── _Attachments/        # 全局附件目录
```

## 导出后的目录结构

```
Wiz_Export/
├── 笔记本1/
│   ├── 笔记1.html
│   ├── 笔记1_files/    # 该笔记的附件
│   └── 笔记2.html
└── 笔记本2/
    └── 笔记3_files/
```

## 系统要求

- Python 3.8+
- 操作系统：Windows / Linux / macOS
- 为知笔记客户端（用于导出）
- 足够的磁盘空间

## 注意事项

1. **备份优先**：迁移前务必备份整个 `My Knowledge` 目录
2. **导出格式**：必须使用"多个网页文件（含附件）"格式
3. **路径安全**：避免路径包含特殊字符或空格
4. **权限要求**：需要读取源目录、写入目标目录的权限
5. **增量复制**：脚本会自动跳过已存在的文件，可安全重复运行

## 常见问题

### Q: 为什么自动检测不到数据目录？

A: 可能是非标准安装路径或中文用户名。请手动输入完整路径。

### Q: 导出的 HTML 文件打不开？

A: 1) 确保用浏览器打开；2) 检查 `_files` 文件夹是否存在；3) 确认文件未被损坏。

### Q: 图片不显示？

A: 检查 `_files` 文件夹是否与 `.html` 文件在同一目录，路径是否为相对路径。

### Q: 附件复制失败？

A: 检查是否有足够的磁盘空间和文件读写权限。

### Q: Pandoc 安装失败怎么办？

A: 
1. Windows: 手动下载安装包 https://github.com/jgm/pandoc/releases/latest
2. macOS: 运行 `brew install pandoc`
3. Linux: 运行 `sudo apt install pandoc` (Ubuntu) 或对应发行版命令

### Q: 转换后的 Markdown 格式不对？

A: 
1. 检查 Pandoc 版本，建议使用最新版本
2. 某些复杂 HTML 可能有兼容性问题，可尝试手动调整
3. 图片路径可能需要手动修复

## 后续步骤

迁移完成后建议：
1. 使用本技能的 Pandoc 转换功能：`convert_with_pandoc()` 或 `interactive_convert()`
2. 导入 Obsidian / Logseq / Notion 等笔记软件
3. 在新笔记系统中建立双向链接
4. 清理重复内容

## License

MIT

---

**注意**：本技能仅作为迁移辅助工具，不对数据丢失负责。请始终保留原始备份，直至确认迁移完成。
