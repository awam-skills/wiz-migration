# 附件插入功能测试文档

## 测试目的

验证 `fix_asset_paths` 函数能够正确处理 Markdown 文件中的 `_Attachments` 引用，将其插入到文件尾部的附件区域中。

## 测试场景

根据用户需求，需要测试以下场景：
1. 从原始目录 `G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习\#学信网.txt#.md` 重新生成
2. 目标目录为 `G:\Data\knowledge\wiz-c\pages\10其他\烂笔头\01记录\02学习\学校学习`
3. 查找对应的 `_Attachments` 目录，将附件插入到 Markdown 文件尾部

## 测试步骤

### 方法 1: 使用快速测试脚本 (推荐)

运行 `quick_test.py` 脚本进行自动化测试：

```bash
cd <技能根目录>
python quick_test.py
```

该脚本会：
1. 创建临时测试目录结构
2. 生成包含 `_Attachments` 引用的 Markdown 文件
3. 执行 `fix_asset_paths` 函数
4. 验证修复结果

**预期结果：**
- ✅ 原文中的 `_Attachments` 引用被移除
- ✅ 文件末尾添加 `## 附件` 区域
- ✅ 附件使用正确的相对路径（根据文件深度计算）
- ✅ 所有附件文件都出现在附件区域中

### 方法 2: 使用单元测试脚本

运行 `test_attachment_unit.py` 进行更全面的测试：

```bash
cd <技能根目录>
python test_attachment_unit.py
```

该脚本测试以下场景：
1. 仅包含 `_files` 引用的文件
2. 仅包含 `_Attachments` 引用的文件
3. 包含混合引用的文件

**预期结果：**
- `_files` 引用被正确转换为 `../assets/` 路径
- `_Attachments` 引用被移除并添加到尾部附件区域
- 路径根据文件深度正确计算

### 方法 3: 手动测试实际文件

1. 确认原始文件存在附件引用：

   ```python
   from pathlib import Path
   import re

   # 读取原始文件
   source_md = Path(r"G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习").glob("*学信网*.md")
   content = source_md.read_text(encoding='utf-8')

   # 查找附件引用
   pattern = r'!\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)'
   matches = re.findall(pattern, content)
   print(f"找到 {len(matches)} 个附件引用")
   ```

2. 确认目标目录存在附件映射：

   ```python
   import json

   mapping_file = Path(r"G:\Data\knowledge\wiz-c\.attachment_mapping.json")
   with open(mapping_file, 'r', encoding='utf-8') as f:
       mapping = json.load(f)

   # 查找对应的笔记映射
   note_name = "#学信网.txt#"  # 文件名（不含扩展名）
   if note_name in mapping:
       attach_dir = mapping[note_name]['attach_dir_name']
       print(f"附件目录: {attach_dir}")
   ```

3. 执行修复：

   ```python
   from logseq_migrator import fix_asset_paths

   pages_dir = Path(r"G:\Data\knowledge\wiz-c\pages")
   stats = fix_asset_paths(pages_dir, mapping)

   print(f"修复: {stats['fixed']} 处")
   print(f"添加附件: {stats['attachments_added']} 个")
   ```

## 验证点

### 1. 相对路径计算

| 文件位置 | 相对深度 | 期望路径前缀 |
|---------|---------|------------|
| `pages/file.md` | 0 | `../assets/` |
| `pages/a/file.md` | 1 | `../../assets/` |
| `pages/a/b/file.md` | 2 | `../../../assets/` |
| `pages/a/b/c/file.md` | 3 | `../../../../assets/` |

### 2. 附件区域格式

```markdown

---

## 附件

![附件名](../../assets/attachments/笔记名_Attachments/文件名)

```

### 3. 附件映射文件格式

`.attachment_mapping.json`:

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

## 功能说明

### fix_asset_paths 函数

**位置:** `scripts/logseq_migrator.py`

**功能:**
1. 遍历 pages 目录下所有 Markdown 文件
2. 计算每个文件的相对深度
3. 处理 `_files` 引用：
   - 替换为 `../assets/` 路径
   - 根据深度调整 `../` 数量
4. 处理 `_Attachments` 引用：
   - 移除原文中的引用
   - 收集附件信息
   - 在文件尾部添加附件区域
   - 使用正确的相对路径指向 `assets/attachments/`

**参数:**
- `pages_dir`: Logseq pages 目录路径
- `attachment_mapping`: 附件映射字典（可选）

**返回:**
- 统计信息字典:
  - `fixed`: 修复的引用数
  - `failed`: 失败数
  - `errors`: 错误列表
  - `attachments_added`: 添加的附件数

## 常见问题

### Q1: 为什么 # 学信网.txt#.md 文件名包含特殊字符？

A: 在为知笔记中，如果原始笔记是导入的文件（如 .txt），文件名会保留原始文件名。`#` 符号在 Windows 文件系统中是有效的。

### Q2: 附件目录名如何确定？

A: 附件目录名默认为 `{笔记名}_Attachments`，可以通过附件映射文件中的 `attach_dir_name` 字段覆盖。

### Q3: 如何确认附件路径是否正确？

A: 检查以下几点：
1. `../` 的数量是否等于 `文件深度 + 1`
2. 路径指向 `assets/attachments/` 目录
3. 文件名与附件映射中的记录一致

## 测试结果

运行 `quick_test.py` 后应该看到：

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

![文档](../../assets/attachments/test_note_Attachments/document.pdf)

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

## 下一步

如果测试通过，可以：
1. 在实际的 wiz-c 项目中运行迁移
2. 检查生成的 Markdown 文件
3. 确认附件路径在 Logseq 中可以正常访问

如果测试失败，请：
1. 检查 `scripts/logseq_migrator.py` 中的 `fix_asset_paths` 函数
2. 确认附件映射文件存在且格式正确
3. 查看错误日志定位问题
