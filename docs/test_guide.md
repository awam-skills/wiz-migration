# 附件插入功能测试指南

## 概述

本文档介绍如何使用测试工具验证为知笔记迁移工具中的附件插入功能。

## 测试工具

### 1. quick_test.py - 快速验证（推荐）

**适用场景：** 快速验证功能是否正常工作

**特点：**
- 自动创建测试数据
- 自动执行并验证
- 自动清理临时文件
- 无需手动输入

**运行方法：**

```bash
cd c:\Users\Administrator\.codebuddy\skills\wiz-migration
python quick_test.py
```

**预期输出：**

```
================================================================================
附件插入功能快速验证
================================================================================

测试目录: C:\Users\ADMINI~1\AppData\Local\Temp\wiz_attach_test_xxx\pages
测试文件: test\deep\path\test_note.md
相对深度: 3 层

原始内容:
------------------------------------------------------------
# 测试笔记

这是一篇测试笔记，包含附件引用。

![图片1](test_note_Attachments/image1.png)
![文档](test_note_Attachments/document.pdf)

正文内容结束。

执行 fix_asset_paths...
    ✅ test_note.md: 修复 2 处路径, 添加 2 个附件引用

统计:
  修复: 2
  添加附件: 2

修复后内容:
================================================================================
# 测试笔记

这是一篇测试笔记，包含附件引用。


正文内容结束。

---

## 附件

![图片1](../../assets/attachments/test_note_Attachments/image1.png)

![文档](../../assets/attachments/test_note_Attachments/document.png)

================================================================================

验证结果:
------------------------------------------------------------
  ❌ 仍包含 _Attachments 引用: False
  ✅ 包含附件区域: True
  ✅ 包含正确的相对路径: True
     期望: ../../assets/attachments/test_note_Attachments/
  ✅ 包含 image1.png: True
  ✅ 包含 document.pdf: True

✅ 所有验证通过！

已清理测试目录: C:\Users\ADMINI~1\AppData\Local\Temp\wiz_attach_test_xxx
================================================================================
```

### 2. test_attachment_unit.py - 完整单元测试

**适用场景：** 需要详细测试各种场景

**特点：**
- 测试多种文件类型
- 深度验证每个功能点
- 保留测试目录供检查
- 交互式清理选项

**运行方法：**

```bash
cd c:\Users\Administrator\.codebuddy\skills\wiz-migration
python test_attachment_unit.py
```

**测试场景：**

1. **仅 _files 引用**
   - 文件：`test_files.md`
   - 验证：转换为 `../assets/` 路径
   - 不添加附件区域

2. **仅 _Attachments 引用**
   - 文件：`test_attachments.md`
   - 验证：移除原文引用，添加尾部附件区域

3. **混合引用**
   - 文件：`test_mixed.md`
   - 验证：同时处理两种类型引用

### 3. test_attachment_simple.py - 交互式测试

**适用场景：** 测试实际文件

**特点：**
- 用户指定源文件路径
- 支持查看实际文件内容
- 详细的输出信息

**运行方法：**

```bash
cd c:\Users\Administrator\.codebuddy\skills\wiz-migration
python test_attachment_simple.py
```

**交互流程：**

1. 输入源 Markdown 文件路径
2. 自动分析文件中的附件引用
3. 选择是否复制到目标目录
4. 选择是否执行修复
5. 查看修复结果

## 实际文件测试示例

### 准备工作

假设你有以下文件：
- 原始文件：`G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习\#学信网.txt#.md`
- 目标目录：`G:\Data\knowledge\wiz-c\pages`
- 附件映射：`G:\Data\knowledge\wiz-c\.attachment_mapping.json`

### 步骤 1: 检查原始文件

```python
from pathlib import Path
import re

source_md = Path(r"G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习")
md_files = list(source_md.glob("*学信网*.md"))

for md in md_files:
    content = md.read_text(encoding='utf-8')
    print(f"\n文件: {md.name}")
    print("=" * 60)
    print(content)

    # 查找附件引用
    pattern = r'!\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)'
    matches = re.findall(pattern, content)
    if matches:
        print(f"\n找到 {len(matches)} 个 _Attachments 引用")
        for alt, note, file in matches:
            print(f"  - {file}")
```

### 步骤 2: 执行迁移

如果还没有迁移，运行：

```bash
cd c:\Users\Administrator\.codebuddy\skills\wiz-migration
python bin\wiz-migrate
```

选择阶段3进行迁移。

### 步骤 3: 验证结果

```python
from pathlib import Path

target_file = Path(r"G:\Data\knowledge\wiz-c\pages\10其他\烂笔头\01记录\02学习\学校学习\#学信网.txt#.md")

if target_file.exists():
    content = target_file.read_text(encoding='utf-8')
    print(content)

    # 检查是否包含附件区域
    if "## 附件" in content:
        print("\n✅ 包含附件区域")
    else:
        print("\n❌ 不包含附件区域")

    # 检查是否移除了 _Attachments 引用
    if "_Attachments/" in content:
        print("❌ 仍包含 _Attachments 引用")
    else:
        print("✅ 已移除 _Attachments 引用")
```

## 功能验证点

### 1. 相对路径计算

验证不同深度的文件路径是否正确：

| 文件位置 | 深度 | 期望路径 |
|---------|------|---------|
| `pages/file.md` | 0 | `../assets/` |
| `pages/a/b/file.md` | 2 | `../../../assets/` |
| `pages/a/b/c/d/file.md` | 4 | `../../../../../assets/` |

**验证方法：**

```python
from pathlib import Path

# 计算深度
file_path = Path("pages/a/b/c/file.md")
rel_path = file_path.relative_to("pages")
depth = len(rel_path.parts) - 1

# 生成路径
assets_prefix = "../" * (depth + 1)
print(f"深度: {depth}")
print(f"路径前缀: {assets_prefix}assets/")
```

### 2. 附件区域格式

验证附件区域格式是否正确：

**期望格式：**

```markdown

---

## 附件

![image1.png](../../assets/attachments/笔记名_Attachments/image1.png)

![doc.pdf](../../assets/attachments/笔记名_Attachments/doc.pdf)

```

### 3. 附件映射文件

验证映射文件格式：

**期望格式：**

```json
{
  "笔记名": {
    "original_rel_path": "相对路径",
    "target_rel_path": "相对路径",
    "attach_dir_name": "笔记名_Attachments",
    "note_name": "笔记名"
  }
}
```

## 故障排查

### 问题 1: 测试脚本无法运行

**可能原因：**
- Python 路径配置问题
- 模块导入失败

**解决方法：**

```bash
# 检查 Python 版本
python --version

# 检查脚本路径
dir c:\Users\Administrator\.codebuddy\skills\wiz-migration

# 尝试直接运行
python c:\Users\Administrator\.codebuddy\skills\wiz-migration\quick_test.py
```

### 问题 2: 附件路径不正确

**可能原因：**
- 深度计算错误
- 路径前缀生成错误

**解决方法：**

检查 `logseq_migrator.py` 中的 `fix_asset_paths` 函数：

```python
# 计算相对深度
rel_path = md_file.relative_to(pages_dir)
depth = len(rel_path.parts) - 1

# 生成路径前缀
if depth > 0:
    assets_prefix = "../" * (depth + 1)
else:
    assets_prefix = "../"
```

### 问题 3: 附件区域未添加

**可能原因：**
- 没有检测到 `_Attachments` 引用
- 映射文件不存在或格式错误

**解决方法：**

1. 确认源文件包含 `_Attachments` 引用
2. 确认附件映射文件存在
3. 检查映射文件中的笔记名是否匹配

```python
import json
from pathlib import Path

mapping_file = Path("G:\\Data\\knowledge\\wiz-c\\.attachment_mapping.json")
with open(mapping_file, 'r', encoding='utf-8') as f:
    mapping = json.load(f)

# 查找笔记名
print(mapping.keys())
```

## 总结

测试流程：

1. **快速验证** → 运行 `quick_test.py`
2. **详细测试** → 运行 `test_attachment_unit.py`
3. **实际测试** → 运行 `test_attachment_simple.py` 或手动测试
4. **验证结果** → 检查生成的 Markdown 文件

如果所有测试通过，说明附件插入功能正常工作！
