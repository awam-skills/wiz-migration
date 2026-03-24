# Markdown 文件复制策略更新

## 问题

在阶段3 Logseq 迁移时，复制 Markdown 文件到 pages 目录，遇到以下问题：

```
✅ Markdown 文件已复制: 0 个
  ⏭️  Markdown 文件已存在跳过: 1827 个
```

当目标 Markdown 文件已存在时，会直接跳过，没有询问用户选择覆盖还是跳过。

## 解决方案

为 `move_markdown_to_pages` 函数添加了文件存在策略询问功能，提供3个选项：

### 策略选项

1. **覆盖 (overwrite)** - 覆盖所有已存在的文件
2. **跳过 (skip)** - 跳过所有已存在的文件
3. **重命名 (rename)** - 自动重命名新文件（添加序号）

**注意：** 策略选择后自动应用到所有文件，不需要区分"单个"和"全部"。

### 用户交互示例

```
⚠️  检测到目标文件已存在
============================================================
请选择处理策略（本次迁移全程有效）:
  1. 覆盖 (overwrite) - 覆盖所有已存在的文件
  2. 跳过 (skip) - 跳过所有已存在的文件
  3. 重命名 (rename) - 自动重命名新文件（添加序号）

请输入选择 (1/2/3): 2
⏭️  已选择: 跳过所有已存在的文件
```


### 输出统计

```
迁移完成!
============================================================
  ✅ 附件已复制到 assets/: 1234 个
  ⏭️  附件已存在跳过: 56 个
  ✅ Markdown 文件已复制: 0 个
  ⏭️  Markdown 文件已存在跳过: 1827 个
  ✅ 路径已修复: 3456 处
```

## 功能特性

### MD5 检查

在询问策略之前，会先检查源文件和目标文件的 MD5：

```python
src_md5 = calculate_md5(md_file)
dest_md5 = calculate_md5(dest_file)
if src_md5 == dest_md5:
    print(f"    ⏭️  内容一致，跳过: {rel_path} (MD5: {src_md5[:8]}...)")
    stats["skipped"] += 1
    continue
```

如果 MD5 一致（内容相同），直接跳过，不询问策略。

### 每次调用重置策略

每次调用 `move_markdown_to_pages` 函数时，会重置 `_file_exists_strategy` 全局变量，确保每次都会重新询问：

```python
def move_markdown_to_pages(source_dir: Path, pages_dir: Path) -> Dict:
    global _file_exists_strategy
    _file_exists_strategy = None  # 重置策略
    ...
```

### 与 Pandoc 转换器一致

此实现与 `pandoc_converter.py` 中的策略逻辑保持一致，提供统一的用户体验。

## 使用场景

### 场景1：增量更新

选择"跳过"（2），保留已有文件，只复制新文件：
```
✅ Markdown 文件已复制: 45 个
⏭️  Markdown 文件已存在跳过: 1827 个
```

### 场景2：完全更新

选择"覆盖"（1），替换所有已有文件：
```
✅ Markdown 文件已复制: 1872 个
⏭️  Markdown 文件已存在跳过: 0 个
```

### 场景3：保留备份

选择"重命名"（3），新文件自动添加序号：
```
✅ 复制: file.md -> pages/
⚠️  重命名: file_1.md
✅ 复制: file.md -> pages/
⚠️  重命名: file_2.md
```


## 相关文件

- `scripts/logseq_migrator.py` - 主实现文件
  - `ask_file_exists_strategy()` - 策略询问函数
  - `move_markdown_to_pages()` - Markdown 文件复制函数
  - `_file_exists_strategy` - 全局策略变量

- `scripts/pandoc_converter.py` - Pandoc 转换器（参考实现）
  - `batch_convert()` - 批量转换函数
  - `batch_convert_with_html2text()` - HTML2Text 批量转换函数

## 总结

此次更新使 Markdown 文件复制功能更加灵活和可控，用户可以根据实际需求选择最适合的策略，避免了数据意外覆盖或遗漏的问题。
