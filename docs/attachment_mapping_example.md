# 附件映射示例

本文档说明 `_Attachments` 目录映射功能的实现细节。

## 背景

在为知笔记迁移过程中，`_Attachments` 目录包含了额外的附件文件。这些附件在原 Markdown 中不存在，需要在转换后添加到文档尾部。

## 映射文件位置

映射文件保存在：`{导出目录}/.attachment_mapping.json`

## 映射结构

```json
{
  "笔记名1": {
    "original_rel_path": "01计算机/01编程学习/笔记名1_Attachments",
    "target_rel_path": "01计算机/01编程学习/笔记名1_Attachments",
    "attach_dir_name": "笔记名1_Attachments",
    "note_name": "笔记名1"
  },
  "笔记名2": {
    "original_rel_path": "02文学/笔记名2_Attachments",
    "target_rel_path": "02文学/笔记名2_Attachments",
    "attach_dir_name": "笔记名2_Attachments",
    "note_name": "笔记名2"
  }
}
```

## 字段说明

- `note_name`: 笔记文件名（不含扩展名）
- `original_rel_path`: 原始相对路径（从源根目录到 _Attachments 目录）
- `target_rel_path`: 目标相对路径（从导出目录到 _Attachments 目录）
- `attach_dir_name`: 附件目录名（例如：`笔记名_Attachments`）

## 使用流程

### 阶段1：附件复制（生成映射）

```python
# migrator.py 中的 _copy_attachments_python 函数
for attach_dir in attachments_dirs:
    # 计算相对路径
    rel_path = attach_dir.relative_to(source)
    dest_path = target / rel_path

    # 记录映射
    note_name = attach_dir.name.replace('_Attachments', '')
    attachment_mapping[note_name] = {
        'original_rel_path': str(rel_path),
        'target_rel_path': str(rel_path),
        'attach_dir_name': attach_dir.name,
        'note_name': note_name
    }

# 保存映射文件
mapping_file = target / ".attachment_mapping.json"
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(attachment_mapping, f, indent=2, ensure_ascii=False)
```

### 阶段3：Markdown 转换（使用映射）

```python
# logseq_migrator.py 中的 fix_asset_paths 函数
# 加载映射
with open(mapping_file, 'r', encoding='utf-8') as f:
    attachment_mapping = json.load(f)

# 处理每个 Markdown 文件
for md_file in md_files:
    note_name = md_file.stem  # 提取笔记名

    # 查找映射信息
    attach_info = attachment_mapping.get(note_name)

    # 使用映射信息构建附件路径
    if attach_info:
        attachment_dir = attach_info['attach_dir_name']
    else:
        attachment_dir = f"{note_name}_Attachments"

    # 添加到文档尾部
    attachment_path = f"{assets_prefix}assets/attachments/{attachment_dir}/{file_name}"
```

## 示例场景

### 场景1：标准结构

```
源目录/
├── all/
│   ├── 01计算机/
│   │   ├── 基本类型和引用类型.md
│   │   └── 基本类型和引用类型_Attachments/
│   │       ├── image1.png
│   │       └── image2.png
```

生成的映射：
```json
{
  "基本类型和引用类型": {
    "original_rel_path": "01计算机/基本类型和引用类型_Attachments",
    "target_rel_path": "01计算机/基本类型和引用类型_Attachments",
    "attach_dir_name": "基本类型和引用类型_Attachments",
    "note_name": "基本类型和引用类型"
  }
}
```

### 场景2：深度嵌套

```
导出目录/
├── pages/
│   └── 01计算机/
│       └── 01编程学习/
│           └── 一天一个知识点-JavaScript/
│               ├── 03.1 基本类型和引用类型.md
│               └── 03.1 基本类型和引用类型_Attachments/
│                   └── image.png
```

生成的映射：
```json
{
  "03.1 基本类型和引用类型": {
    "original_rel_path": "01计算机/01编程学习/一天一个知识点-JavaScript/03.1 基本类型和引用类型_Attachments",
    "target_rel_path": "01计算机/01编程学习/一天一个知识点-JavaScript/03.1 基本类型和引用类型_Attachments",
    "attach_dir_name": "03.1 基本类型和引用类型_Attachments",
    "note_name": "03.1 基本类型和引用类型"
  }
}
```

Markdown 文件中的附件引用：
```markdown
## 附件

![image.png](../../../assets/attachments/03.1 基本类型和引用类型_Attachments/image.png)
```

## 优势

1. **准确性**：通过映射关系，确保每个 Markdown 文件正确匹配到对应的 `_Attachments` 目录
2. **灵活性**：支持重命名、跳过等策略后，映射自动更新目标路径
3. **可追溯**：保留原始路径信息，便于问题排查
4. **自动化**：无需手动匹配，系统自动根据笔记名查找对应附件

## 注意事项

- 映射文件在附件复制阶段生成
- 如果映射文件不存在，Markdown 转换阶段会回退到默认规则（笔记名_Attachments）
- 笔记名匹配基于文件名（不含扩展名），确保唯一性
