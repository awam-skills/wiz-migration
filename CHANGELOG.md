# 为知笔记迁移技能更新日志

## 2026-03-24 更新

### ✅ 新增功能

#### 0. 简化文件冲突处理策略

**问题描述：**
- 原先提供5个选项：覆盖（当前）、跳过（当前）、覆盖所有、跳过所有、重命名
- "仅当前"和"所有"的区别让用户困惑，实际上用户通常希望策略应用到全部文件

**解决方案：**
- 简化为3个选项：覆盖（所有）、跳过（所有）、重命名
- 选择后的策略自动应用到所有冲突文件，无需区分单个还是全部

#### 1. 重新设计 _Attachments 添加策略（完全独立于阶段1）

**问题描述：**
- 旧策略依赖阶段1生成的 `.attachment_mapping.json`
- 如果阶段1没有执行或映射文件丢失，阶段3就无法添加附件区域
- 用户报告：即使已经将 _Attachments 复制到 `assets/attachments`，Markdown 文件中仍没有附件区域

**新策略（完全独立）：**
```
阶段3: Logseq 迁移
  ↓
  步骤1: 复制附件到 assets/
  步骤2: 复制 Markdown 到 pages/
  步骤3: 添加附件区域（新增）
    - 扫描 assets/attachments 目录下的所有子目录
    - 对每个子目录（如 "笔记名_Attachments"）：
      1. 解析出对应的 Markdown 文件名
         "assets/attachments/#学信网.txt#_Attachments" → "#学信网.txt#.md"
      2. 在 pages/ 目录中递归查找匹配的 .md 文件
      3. 收集该目录下的所有文件
      4. 在 Markdown 文件尾部添加附件区域，引用这些文件
  步骤4: 修复 _files 路径
```

**核心改动：**
- **完全不依赖** `.attachment_mapping.json`
- 直接从 `assets/attachments` 目录扫描
- 通过目录名自动匹配 Markdown 文件
- 自动计算正确的相对路径（根据 Markdown 文件的深度）

**实现细节：**
- 目录名解析规则：`笔记名_Attachments` → `笔记名.md`
- 递归搜索 pages 目录查找匹配的 Markdown 文件
- 收集附件目录中的所有文件（包括子目录）
- 生成正确的相对路径（`../assets/attachments/...`）

**代码修改：**
- `scripts/add_attachments.py`: 独立的附件添加工具（可直接运行）
- `scripts/logseq_migrator.py`:
  - 新增步骤3：`_add_attachments_from_assets()`
  - 新增辅助函数：
    - `_parse_attach_dir_to_md_name()`: 解析目录名到 Markdown 文件名
    - `_find_md_file_for_attach_dir()`: 在 pages 中查找匹配的 Markdown
    - `_collect_attachments_from_dir()`: 收集附件文件
    - `_add_attachment_section_to_md()`: 在 Markdown 中添加附件区域
  - 新增统计字段：
    - `attach_dirs_processed`: 处理的附件目录数
    - `attach_dirs_not_found`: 未找到对应 Markdown 的目录数
    - `attach_dirs_failed`: 处理失败的目录数
  - 修改步骤3为"添加附件区域"
  - 将原来的路径修复改为步骤4"修复 _files 路径"

**用户交互：**
```
迁移完成!
============================================================
  ✅ 附件已复制到 assets/: 1234 个
  ⏭️  附件已存在跳过: 56 个

  📎 附件区域添加:
    📂 处理的附件目录: 100 个
    ✅ 已添加附件引用: 345 个
    ⚠️  未找到对应 Markdown: 10 个

  ✅ Markdown 文件已复制: 1872 个
  ✅ 路径已修复 (_files): 3456 处
```

**优势：**
1. ✅ 完全独立，不依赖阶段1
2. ✅ 可以随时运行，无需重新导出
3. ✅ 即使附件目录已存在，也能为对应 Markdown 添加引用
4. ✅ 逻辑简单直接，易于理解和维护





**问题描述：**
- 原先提供5个选项：覆盖（当前）、跳过（当前）、覆盖所有、跳过所有、重命名
- "仅当前"和"所有"的区别让用户困惑，实际上用户通常希望策略应用到全部文件

**解决方案：**
- 简化为3个选项：覆盖（所有）、跳过（所有）、重命名
- 选择后的策略自动应用到所有冲突文件，无需区分单个还是全部

**用户交互：**
```
⚠️  检测到目标文件已存在
============================================================
请选择处理策略（本次迁移全程有效）:
  1. 覆盖 (overwrite) - 覆盖所有已存在的文件
  2. 跳过 (skip) - 跳过所有已存在的文件
  3. 重命名 (rename) - 自动重命名新文件（添加序号）

请输入选择 (1/2/3):
```

**代码修改：**
- `ask_file_exists_strategy()` 函数简化策略选项
- 内部直接使用 `overwrite_all`、`skip_all` 等统一策略
- 策略处理逻辑合并相同选项的分支



#### 1. 阶段1自动集成 _Attachments 复制

**问题描述：**
- 原先在阶段1（导出为知笔记）后，不会自动复制原始的 `_Attachments` 目录
- 用户需要手动操作或使用未调用的 `step3_attachment_migration()` 函数

**解决方案：**
- 在 `run_stage1()` 函数中增加了附件复制步骤
- 用户导出 HTML 完成后，会询问是否自动复制 `_Attachments` 目录

**执行流程：**
```
阶段1: 导出为知笔记
  ↓
  1. 检测数据目录和导出目录
  2. 显示导出指南
  3. 等待用户手动导出 HTML
  4. 【新增】询问是否复制 _Attachments 目录
  5. 【新增】如果选择是，调用 run_attachment_migration() 复制附件
  6. 显示复制结果统计
```

**用户交互：**
```
是否自动复制 _Attachments 目录？(y/n): y

正在复制 _Attachments 目录...
源目录: G:\Data\knowledge\wiz
目标目录: G:\Data\knowledge\wiz-b\assets

统计:
  ✅ 复制成功: 1,234 个
  ❌ 复制失败: 0 个
```

#### 2. 添加附件插入测试功能

**问题描述：**
- 需要验证附件插入功能是否正常工作
- 用户希望测试从原始文件重新生成并插入附件的完整流程

**解决方案：**
- 添加了 `quick_test.py` 快速验证脚本
- 添加了 `test_attachment_unit.py` 单元测试脚本
- 添加了 `test_attachment_simple.py` 交互式测试脚本
- 创建了详细的测试文档 `docs/attachment_insertion_test.md`

**测试文件：**
1. `quick_test.py` - 快速验证脚本（推荐）
   - 创建临时测试数据
   - 自动执行修复
   - 验证结果
   - 自动清理

2. `test_attachment_unit.py` - 完整单元测试
   - 测试 `_files` 引用处理
   - 测试 `_Attachments` 引用处理
   - 测试混合引用场景
   - 验证相对路径计算

3. `test_attachment_simple.py` - 交互式测试
   - 用户指定源文件
   - 支持实际文件测试
   - 详细的输出信息

**使用方法：**
```bash
# 快速测试
python quick_test.py

# 完整单元测试
python test_attachment_unit.py

# 交互式测试
python test_attachment_simple.py
```

**预期结果：**
- ✅ 原文中的 `_Attachments` 引用被移除
- ✅ 文件末尾添加 `## 附件` 区域
- ✅ 附件使用正确的相对路径（根据文件深度计算）
- ✅ 路径格式：`../../assets/attachments/笔记名_Attachments/文件名`

### 🐛 Bug 修复

#### 1. 修复 _Attachments 引用移除失败问题

**问题描述：**
- 测试显示 `_Attachments` 引用没有被完全移除
- 验证失败：`❌ 仍包含 _Attachments 引用: True`

**原因：**
- 原先使用字符串替换 `content.replace()` 方式不正确
- 当 `alt_text` 为空时，构建的模式无法正确匹配

**解决方案：**
- 改用 `re.sub()` 直接替换，一次性移除所有匹配
- 添加空行清理逻辑：`content = re.sub(r'\n\n+', '\n\n', content)`

**修改位置：**
- `scripts/logseq_migrator.py` 的 `fix_asset_paths` 函数

**修改前：**
```python
for prefix, alt_text, note_name, file_name in matches_attach:
    old_pattern = f"{prefix}[{alt_text}]({note_name}_Attachments/{file_name})"
    attachments_to_add.append(file_name)
    content = content.replace(old_pattern, '')
    content = re.sub(r'^\s*$', '\n', content)
```

**修改后：**
```python
for prefix, alt_text, note_name, file_name in matches_attach:
    attachments_to_add.append(file_name)

# 使用正则替换一次性移除所有 _Attachments 引用
content = pattern_attach.sub('', content)

# 清理可能产生的多余空行
content = re.sub(r'\n\n+', '\n\n', content)
content = content.strip()
```

#### 2. 增强 Markdown 文件复制策略

**问题描述：**
- Markdown 文件复制到 Logseq pages 目录时，遇到已存在文件会直接跳过
- 用户无法选择覆盖或跳过的策略
- 缺少"覆盖所有"和"跳过所有"选项

**解决方案：**
- 添加策略询问功能，提供5个选项：
  1. 覆盖 (overwrite) - 仅覆盖当前文件
  2. 跳过 (skip) - 仅跳过当前文件
  3. 覆盖所有 (overwrite_all) - 覆盖所有已存在的文件
  4. 跳过所有 (skip_all) - 跳过所有已存在的文件
  5. 重命名 (rename) - 自动重命名新文件

- 每次调用 `move_markdown_to_pages` 时重置策略，重新询问

**修改位置：**
- `scripts/logseq_migrator.py` 的 `ask_file_exists_strategy` 函数
- `scripts/logseq_migrator.py` 的 `move_markdown_to_pages` 函数

**用户交互：**
```
⚠️  检测到目标文件已存在
============================================================
请选择处理策略（本次迁移全程有效）:
  1. 覆盖 (overwrite) - 仅覆盖当前文件
  2. 跳过 (skip) - 仅跳过当前文件
  3. 覆盖所有 (overwrite_all) - 覆盖所有已存在的文件
  4. 跳过所有 (skip_all) - 跳过所有已存在的文件
  5. 重命名 (rename) - 自动重命名新文件（添加序号）

请输入选择 (1/2/3/4/5): 4
⏭️  已选择: 跳过所有已存在的文件
```

**输出统计：**
```
  ✅ Markdown 文件已复制: 0 个
  ⏭️  Markdown 文件已存在跳过: 1827 个
```
- 添加了 `test_attachment_simple.py` 交互式测试脚本
- 创建了详细的测试文档 `docs/attachment_insertion_test.md`

**测试文件：**
1. `quick_test.py` - 快速验证脚本（推荐）
   - 创建临时测试数据
   - 自动执行修复
   - 验证结果
   - 自动清理

2. `test_attachment_unit.py` - 完整单元测试
   - 测试 `_files` 引用处理
   - 测试 `_Attachments` 引用处理
   - 测试混合引用场景
   - 验证相对路径计算

3. `test_attachment_simple.py` - 交互式测试
   - 用户指定源文件
   - 支持实际文件测试
   - 详细的输出信息

**使用方法：**
```bash
# 快速测试
python quick_test.py

# 完整单元测试
python test_attachment_unit.py

# 交互式测试
python test_attachment_simple.py
```

**预期结果：**
- ✅ 原文中的 `_Attachments` 引用被移除
- ✅ 文件末尾添加 `## 附件` 区域
- ✅ 附件使用正确的相对路径（根据文件深度计算）
- ✅ 路径格式：`../../assets/attachments/笔记名_Attachments/文件名`

============================================================
附件复制
============================================================

为知笔记的原始 _Attachments 目录包含额外的附件文件
导出 HTML 时只会生成 _files 目录
是否将 _Attachments 目录复制到导出目录？

是否复制 _Attachments 目录？（建议复制）(y/n): y

正在复制 _Attachments 目录...
============================================================
复制结果:
  ✅ 成功复制: 15 个
  ⏭️  已存在跳过: 3 个
  ❌ 失败: 0 个
============================================================

✅ _Attachments 目录复制完成
```

---

### 🐛 Bug 修复

#### 修复1：_Attachments 复制源目录检测错误

**问题描述：**
- 为知笔记数据目录结构：`Data\账号\all\笔记本分类`
- 原代码直接使用 `Data\账号` 作为源目录进行一致性检查
- 导致检测到大量无关目录（如 `.wizfulltextindex`、`Deleted Items` 等）
- 提示用户选择是否继续，造成困扰

**错误示例：**
```
============================================================
⚠️  检测到目标路径与原始路径内文件不一致
============================================================

仅在源目录存在的目录 (5 个):
  - .wizfulltextindex
  - Deleted Items
  - My Journals
  - My Notes
  - all

仅在目标目录存在的目录 (11 个):
  - 01计算机
  - 02学习
  - 03工作
  ...
```

**解决方案：**

1. **自动检测 all 子目录**（`wiz-migrate` 第 266-278 行）
   ```python
   # 检查 data_dir 是否包含 all 子目录
   source_path = Path(data_dir)
   all_dir = source_path / "all"

   # 如果存在 all 子目录，使用 all 目录作为源目录
   if all_dir.exists() and all_dir.is_dir():
       print(f"✅ 检测到 all 子目录，将从 all 目录复制附件")
       actual_source_dir = str(all_dir)
   else:
       actual_source_dir = data_dir
   ```

2. **智能跳过一致性检查**（`migrator.py` 第 226-235 行）
   ```python
   # 检查是否为 all 目录（为知笔记的笔记目录）
   is_all_dir = source.name == "all" or (source.parent.name == "all")

   if not is_all_dir:
       # 检查目录一致性（仅在非 all 目录时检查）
       if not check_directory_consistency(source, target):
           stats["cancelled"] = True
           return stats
   else:
       print("✅ 检测到为知笔记 all 目录，跳过结构一致性检查")
   ```

**修复后效果：**
```
正在复制 _Attachments 目录...
✅ 检测到 all 子目录，将从 all 目录复制附件
源目录: C:\Users\Administrator\Documents\My Knowledge\Data\wangnew2013@126.com\all
目标目录: G:\Data\Wiz_Export

✅ 检测到为知笔记 all 目录，跳过结构一致性检查

找到 15 个附件目录
```

---

### 📋 完整的附件处理流程

#### 修复前的流程：
```
阶段1（导出）→ 生成 _files 目录（由为知笔记导出）
              ↓
            [缺失] _Attachments 未被复制
              ↓
阶段2（转换）→ 只处理 _files 引用
              ↓
阶段3（导入）→ 从导出目录复制附件到 assets
              ↓
            问题：_Attachments 缺失
```

#### 修复后的流程：
```
阶段1（导出）→ 生成 _files 目录（由为知笔记导出）
              ↓
            [修复] 自动检测 all 子目录
              ↓
            [修复] 从 all 目录复制 _Attachments
              ↓
            [修复] 跳过不必要的一致性检查
              ↓
阶段2（转换）→ 处理 _files 引用
              ↓
阶段3（导入）→ 复制 _files 和 _Attachments 到 assets
              ↓
            完成：所有附件齐全
```

---

### 🎯 附件类型说明

| 类型 | 来源 | 处理方式 | 目标位置 |
|------|------|---------|---------|
| `_files` | 为知笔记导出时自动生成 | 导出时就存在 | 阶段3 复制到 assets/ |
| `_Attachments` | 为知笔记原始数据目录/all | **阶段1 从 all 目录复制** | 阶段3 复制到 assets/attachments/ |

---

### 🔧 代码变更

#### 文件1：`bin/wiz-migrate`

**修改位置1：** 第 261-284 行（`run_stage1()` 函数）
- 附件复制步骤

**修改位置2：** 第 266-278 行（新增逻辑）
- 自动检测 all 子目录
- 使用 all 目录作为源目录进行复制

**主要变更：**
```python
# 检查 data_dir 是否包含 all 子目录
source_path = Path(data_dir)
all_dir = source_path / "all"

# 如果存在 all 子目录，使用 all 目录作为源目录
if all_dir.exists() and all_dir.is_dir():
    print(f"✅ 检测到 all 子目录，将从 all 目录复制附件")
    actual_source_dir = str(all_dir)
else:
    actual_source_dir = data_dir

result = run_attachment_migration(
    source_dir=actual_source_dir,
    target_dir=export_dir
)
```

#### 文件2：`scripts/migrator.py`

**修改位置：** 第 214-242 行（`_copy_attachments_python()` 函数）

**主要变更：**
```python
# 检查是否为 all 目录（为知笔记的笔记目录）
is_all_dir = source.name == "all" or (source.parent.name == "all")

if not is_all_dir:
    # 检查目录一致性（仅在非 all 目录时检查）
    if not check_directory_consistency(source, target):
        stats["cancelled"] = True
        return stats
else:
    print("✅ 检测到为知笔记 all 目录，跳过结构一致性检查")
```

---

### ✨ 其他改进

#### 改进1：默认执行全部阶段

**修改前：**
- 用户必须输入阶段编号（如 1,2,3）
- 直接按回车会提示无效输入

**修改后：**
- 直接按回车默认执行全部阶段（1,2,3）
- 提示文案更新：`"请输入阶段编号（支持多选，如 1,2 或 1,2,3，直接回车默认执行全部）"`

**修改位置：** 第 787-795 行

---

### 📊 使用示例

#### 示例1：执行完整迁移流程（推荐）
```bash
# 启动向导
python wiz-migrate

# 直接按回车，默认执行全部阶段
请输入阶段编号（支持多选，如 1,2 或 1,2,3，直接回车默认执行全部）: [Enter]

# 阶段1完成后，选择复制 _Attachments
============================================================
附件复制
============================================================

为知笔记的原始 _Attachments 目录包含额外的附件文件
导出 HTML 时只会生成 _files 目录
是否将 _Attachments 目录复制到导出目录？

是否复制 _Attachments 目录？（建议复制）: y

正在复制 _Attachments 目录...
✅ 检测到 all 子目录，将从 all 目录复制附件
源目录: C:\Users\Administrator\Documents\My Knowledge\Data\wangnew2013@126.com\all
目标目录: G:\Data\Wiz_Export

✅ 检测到为知笔记 all 目录，跳过结构一致性检查

找到 15 个附件目录
============================================================
复制结果:
  ✅ 成功复制: 15 个
  ⏭️  已存在跳过: 0 个
  ❌ 失败: 0 个
============================================================

✅ _Attachments 目录复制完成

# 继续完成阶段2和阶段3
```

#### 示例2：只执行阶段1和附件复制
```bash
python wiz-migrate

# 只选择阶段1
请输入阶段编号: 1

# 阶段1完成后，选择复制 _Attachments
是否复制 _Attachments 目录？（建议复制）: y
```

---

### 🐛 已知问题

1. `step3_attachment_migration()` 函数仍然存在但未使用
   - 功能已被集成到 `run_stage1()` 中
   - 可以考虑删除或保留作为独立调用选项

2. 目录一致性检查在某些情况下误报（已修复）
   - 修复前：会检查账号目录下的所有子目录
   - 修复后：检测到 all 目录时自动跳过检查

---

### 🔍 技术细节

#### 为知笔记目录结构

```
My Knowledge/
├── Data/
│   └── wangnew2013@126.com/          ← 检测到的数据目录
│       ├── index/
│       ├── attachments/
│       ├── .wizfulltextindex/        ← 不需要复制
│       ├── Deleted Items/            ← 不需要复制
│       └── all/                     ← 实际笔记目录（从这里复制 _Attachments）
│           ├── 01计算机/
│           │   ├── 笔记1.md
│           │   ├── 笔记1_files/      ← 导出时生成
│           │   └── 笔记1_Attachments/ ← 需要复制
│           ├── 02学习/
│           └── ...
```

#### `run_attachment_migration()` 参数说明

```python
result = run_attachment_migration(
    source_dir=actual_source_dir,  # 修复：使用 all 目录
                                  # 例: C:\Users\...\Data\账号\all
                                  # 修复前: C:\Users\...\Data\账号
    target_dir=export_dir          # 导出目录
                                  # 例: G:\Data\Wiz_Export
)
```

**返回值：**
```python
{
    "copied": 15,      # 成功复制的数量
    "skipped": 0,      # 已存在跳过的数量
    "failed": 0,       # 失败的数量
    "cancelled": False # 是否被用户取消
}
```

---

### 📝 后续优化建议

1. **添加进度条**：显示附件复制的实时进度
2. **并行复制**：使用多线程加速大文件复制
3. **校验机制**：复制后校验文件完整性（MD5）
4. **增量更新**：只复制新增或修改的文件
5. **批量重试**：失败的文件自动重试机制

---

### ✅ 测试建议

测试步骤：
1. 运行完整迁移流程（1,2,3）
2. 验证 `_Attachments` 是否被复制到导出目录
3. 验证不再显示误导性的目录不一致提示
4. 验证阶段3中是否正确处理了 `_Attachments`
5. 测试跳过附件复制的情况
6. 测试没有 all 子目录的情况（兼容旧版本）

测试用例：
```bash
# 测试1：完整流程（有 all 子目录）
python wiz-migrate
[Enter]
y  # 复制 _Attachments

# 测试2：完整流程（跳过附件复制）
python wiz-migrate
[Enter]
n  # 不复制 _Attachments

# 测试3：只执行阶段1
python wiz-migrate
1
y  # 复制 _Attachments

# 测试4：直接调用 migrator（传入 all 目录）
python -c "from migrator import run_attachment_migration; print(run_attachment_migration('C:\\...\\all', 'G:\\...'))"
```

---

### 📈 性能影响

- **复制速度**：无影响（只改变源目录）
- **用户体验**：显著提升（避免误导性提示）
- **兼容性**：向后兼容（如果没有 all 子目录，使用原逻辑）

---

**版本：** 1.2.0
**更新日期：** 2026-03-24
**维护者：** CodeBuddy AI Assistant

---

## 2026-03-24 补充更新

### 🐛 Bug 修复

#### 修复 3: Logseq 迁移路径记忆功能失效

**问题描述：**
- 在阶段3 Logseq 迁移时，输入"转换后导出路径"后，下次运行时没有记住上次的输入
- 每次都需要重新手动输入路径，用户体验不佳

**原因：**
- `bin/wiz-migrate` 第382-386行中，硬编码了默认值 `'G:\\Data\\knowledge\\wiz-b'`
- 代码优先使用了硬编码的默认值，忽略了配置文件中保存的记忆值

**错误代码：**
```python
graph_dir = get_user_input(
    "\n请输入转换后导出路径",
    remember_key='logseq_graph_dir',
    default='G:\\Data\\knowledge\\wiz-b'  # ❌ 硬编码默认值覆盖了记忆值
)
```

**解决方案：**

1. **移除硬编码默认值**（第382-386行）
   ```python
   # 修复前
   graph_dir = get_user_input(
       "\n请输入转换后导出路径",
       remember_key='logseq_graph_dir',
       default='G:\\Data\\knowledge\\wiz-b'
   )

   # 修复后
   graph_dir = get_user_input(
       "\n请输入转换后导出路径",
       remember_key='logseq_graph_dir'
   )
   ```

2. **添加智能默认值建议**（第377-389行）
   ```python
   # 尝试从配置中获取记忆值
   remembered_graph_dir = _config.get('logseq_graph_dir')
   if remembered_graph_dir:
       # 有记忆值，直接使用（会显示在提示中）
       graph_dir = get_user_input(
           "\n请输入转换后导出路径",
           remember_key='logseq_graph_dir'
       )
   else:
       # 首次使用，建议使用导出目录
       suggested_dir = export_dir
       print(f"\n💡 建议的输出路径: {suggested_dir}")
       graph_dir = get_user_input(
           "请输入转换后导出路径（直接回车使用建议路径）",
           default=suggested_dir,
           remember_key='logseq_graph_dir'
       )
   ```

3. **修复循环中的硬编码值**（第402、418、420行）
   - 移除了所有 `default='G:\\Data\\knowledge\\wiz-b'` 硬编码
   - 统一使用 `remember_key='logseq_graph_dir'` 让函数自动处理记忆

**修复后效果：**

**首次使用：**
```
💡 建议的输出路径: G:\Data\knowledge\wiz-b
请输入转换后导出路径（直接回车使用建议路径） [G:\Data\knowledge\wiz-b]: [Enter]
✅ 转化后导出目录验证通过: G:\Data\knowledge\wiz-b
```

**再次使用：**
```
请输入转换后导出路径 [G:\Data\knowledge\wiz-b]: [Enter]
✅ 转化后导出目录验证通过: G:\Data\knowledge\wiz-b
```

**输入新路径：**
```
请输入转换后导出路径 [G:\Data\knowledge\wiz-b]: G:\Data\knowledge\wiz-c
✅ 转化后导出目录验证通过: G:\Data\knowledge\wiz-c
```

**第三次使用：**
```
请输入转换后导出路径 [G:\Data\knowledge\wiz-c]: [Enter]
✅ 转化后导出目录验证通过: G:\Data\knowledge\wiz-c
```

**配置文件内容：**
```json
{
  "data_dir": "C:\\Users\\Administrator\\Documents\\My Knowledge\\Data\\wangnew2013@126.com",
  "export_dir": "G:\\Data\\knowledge\\wiz",
  "logseq_graph_dir": "G:\\Data\\knowledge\\wiz-c",
  "converter_choice": "A"
}
```

---

### 🔧 相关改进

#### 改进：路径记忆机制说明

**记忆功能工作原理：**

1. **配置文件位置：** `~/.wiz-migration/config.json`
2. **记忆键名：**
   - `data_dir` - 为知笔记数据目录
   - `export_dir` - 导出目录
   - `logseq_graph_dir` - Logseq 图表目录
   - `converter_choice` - 转换方案选择
   - `output_dir` - Markdown 输出目录
   - `obsidian_vault` - Obsidian Vault 目录

3. **记忆逻辑：**
   ```python
   def get_user_input(prompt, default=None, remember_key=None):
       # 1. 没有默认值但有记忆值 → 使用记忆值
       if default is None and remember_key:
           default = _config.get(remember_key)

       # 2. 有默认值 → 显示在提示中
       if default:
           response = input(f"{prompt} [{default}]: ").strip()
           result = response if response else default
       else:
           result = input(f"{prompt}: ").strip()

       # 3. 有记忆键且有输入 → 保存记忆
       if remember_key and result:
           _config.set(remember_key, result)

       return result
   ```

4. **用户行为：**
   - 直接按回车 → 使用默认值（记忆值）
   - 输入新值 → 保存新值到配置文件
   - 下次使用 → 显示上次输入的值

---

### 📋 影响范围

**修改的文件：**
- `bin/wiz-migrate` - 第 377-420 行

**影响的功能：**
- 阶段3 Logseq 迁移路径输入
- 配置记忆功能

**不影响的功能：**
- 阶段1 导出为知笔记
- 阶段2 转换为 Markdown
- 其他路径记忆（data_dir、export_dir 等）

---

### ✅ 测试验证

**测试步骤：**
1. 首次运行 Logseq 迁移，输入路径 `G:\Data\knowledge\wiz-a`
2. 第二次运行，验证提示中显示 `[G:\Data\knowledge\wiz-a]`
3. 直接按回车，验证使用了记忆值
4. 输入新路径 `G:\Data\knowledge\wiz-b`
5. 第三次运行，验证提示中显示 `[G:\Data\knowledge\wiz-b]`
6. 检查配置文件，确认 `logseq_graph_dir` 值正确更新

**预期结果：**
- ✅ 首次使用时显示建议路径
- ✅ 再次使用时显示上次的输入
- ✅ 直接按回车使用记忆值
- ✅ 输入新值后保存到配置
- ✅ 配置文件正确更新

---

### 📝 版本信息

**修复版本：** 1.2.1
**修复日期：** 2026-03-24
**修复类型：** Bug 修复（用户体验改进）
**严重程度：** 低（不影响功能，但影响使用体验）

---

## 2026-03-24 补充更新（附件显示格式修复）

### 🐛 Bug 修复

#### 修复 4: 附件显示格式改为链接而非图片

**问题描述：**
- 附件以图片格式 `![文件名](路径)` 显示
- 对于非图片文件（PDF、TXT、DOC 等）显示不合适
- 用户希望附件显示为可点击的链接格式

**解决方案：**
- 将附件格式从图片格式改为链接格式
- 移除感叹号，使用 `[文件名](路径)` 格式

**修改位置：**
- `scripts/logseq_migrator.py` 第729行
- `scripts/add_attachments.py` 第110行

**修改前：**
```python
attachment_section += f"![{file_name}]({attachment_path})\n\n"
```

**修改后：**
```python
attachment_section += f"[{file_name}]({attachment_path})\n\n"
```

---

#### 修复 5: 附件区域重复添加问题

**问题描述：**
- 附件区域被重复添加，导致内容重复
- 出现多个 `---` 和 `## 附件` 标题

**问题示例：**
```markdown
---

## 附件

---

## 附件

[#学信网.txt#](../../../../../../assets/attachments/#学信网.txt#_Attachments/#学信网.txt#)
```

**原因：**
- 正则表达式 `r'\n\n## 附件\n\n.*?(?=\n\n## |\n\n---\n\n$|$)'` 无法正确匹配整个附件区域
- 导致替换时只替换了部分内容，留下重复的标题和分隔线

**解决方案：**
- 改用 `re.search()` 查找附件区域的开始位置
- 从附件区域开始截取，移除旧内容
- 添加新的附件区域

**修改前：**
```python
if "## 附件" in content:
    # 替换已有的附件区域
    pattern = r'\n\n## 附件\n\n.*?(?=\n\n## |\n\n---\n\n$|$)'
    new_content = re.sub(pattern, attachment_section.strip() + "\n\n", content, flags=re.DOTALL)
```

**修改后：**
```python
if "## 附件" in content:
    # 查找附件区域的开始位置
    attach_match = re.search(r'\n\n## 附件\n', content)
    if attach_match:
        # 从附件区域开始截取，移除旧内容
        content = content[:attach_match.start()]
        # 添加新的附件区域
        content += attachment_section
        md_file.write_text(content, encoding='utf-8')
```

**修改位置：**
- `scripts/logseq_migrator.py` 第731-744行
- `scripts/add_attachments.py` 第113-125行

**修复后效果：**
```markdown
---

## 附件

[#学信网.txt#](../../../../../../assets/attachments/#学信网.txt#_Attachments/#学信网.txt#)
```

---

### ✨ 改进效果

**格式改进：**
- ✅ 附件以链接形式显示，可点击访问
- ✅ 适合所有文件类型（PDF、TXT、DOC、图片等）
- ✅ 更符合附件的使用场景

**重复问题修复：**
- ✅ 附件区域只显示一次
- ✅ 不会出现重复的 `---` 和 `## 附件` 标题
- ✅ 更新附件时正确替换旧内容

---

**修复版本：** 1.2.2
**修复日期：** 2026-03-24
**修复类型：** Bug 修复（显示格式 + 内容重复）
**严重程度：** 中（影响用户体验）

