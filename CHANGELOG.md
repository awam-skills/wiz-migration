# 为知笔记迁移技能更新日志

## 2026-03-24 更新

### ✅ 新增功能

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
