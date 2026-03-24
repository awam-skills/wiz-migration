# 测试脚本说明

本目录包含用于测试为知笔记迁移工具的测试脚本。

## 测试脚本列表

### quick_test.py ⭐ 推荐使用

**描述：** 快速验证附件插入功能的自动化测试脚本

**特点：**
- ✅ 自动创建测试数据
- ✅ 自动执行功能测试
- ✅ 自动验证结果
- ✅ 自动清理临时文件
- ⚡ 快速、简单、无需交互

**适用场景：**
- 快速验证功能是否正常
- 代码修改后的回归测试
- CI/CD 自动化测试

**使用方法：**
```bash
python quick_test.py
```

**预期时间：** < 5 秒

---

### test_attachment_unit.py

**描述：** 完整的单元测试脚本

**特点：**
- 📋 测试多种文件类型（_files、_Attachments、混合）
- 📊 详细的测试结果报告
- 🗂️ 保留测试目录供检查
- 🧹 交互式清理选项

**适用场景：**
- 全面测试所有功能点
- 开发调试时使用
- 需要检查中间结果

**使用方法：**
```bash
python test_attachment_unit.py
```

**预期时间：** ~10 秒

---

### test_attachment_simple.py

**描述：** 交互式测试脚本

**特点：**
- 🎯 支持指定实际文件路径
- 📝 详细的输出信息
- 🔍 分析文件内容
- 💡 提供操作建议

**适用场景：**
- 测试实际的为知笔记文件
- 需要查看详细信息
- 手动排查问题

**使用方法：**
```bash
python test_attachment_simple.py
```

按提示输入文件路径和选项。

---

### test_attachment_insertion.py

**描述：** 完整的附件插入测试（带路径处理）

**特点：**
- 🎯 针对特定文件测试（如 #学信网.txt#.md）
- 📁 支持创建目标目录结构
- 🔧 完整的迁移流程模拟

**注意：** 由于路径中包含特殊字符（#），可能需要手动处理路径。

**使用方法：**
```bash
python test_attachment_insertion.py
```

---

### test_funcs.py

**描述：** 基础功能导入测试

**特点：**
- ✅ 测试模块导入
- 🔍 检查函数可用性
- 📝 简单输出结果

**适用场景：**
- 首次安装后测试
- 验证环境配置
- 快速检查基础功能

**使用方法：**
```bash
python test_funcs.py
```

---

### test_import.py

**描述：** 包导入测试

**特点：**
- 📦 测试包级导入
- 🔍 检查导出函数
- 📊 显示版本信息

**适用场景：**
- 验证包安装
- 检查接口完整性
- CI 测试

**使用方法：**
```bash
python test_import.py
```

---

### test_imports.py

**描述：** 模块导入测试（简化版）

**特点：**
- ⚡ 快速测试模块导入
- ✅ 简单的 OK/FAILED 输出

**适用场景：**
- 快速检查模块
- 开发调试

**使用方法：**
```bash
python test_imports.py
```

---

## 测试流程建议

### 快速验证（日常开发）

```bash
python quick_test.py
```

### 全面测试（功能开发）

```bash
python test_attachment_unit.py
```

### 实际测试（用户场景）

```bash
python test_attachment_simple.py
```

### 环境检查（首次安装）

```bash
python test_imports.py
python test_import.py
```

---

## 文档

详细的测试指南和说明请参考：

- [测试指南](../docs/test_guide.md)
- [附件插入功能测试](../docs/attachment_insertion_test.md)

---

## 常见问题

### Q: 测试脚本无法运行？

A: 确保已安装 Python 3.6+，并正确配置了路径。

### Q: quick_test.py 执行后没有输出？

A: 检查 Python 脚本执行权限，尝试使用绝对路径运行。

### Q: test_attachment_simple.py 需要输入什么？

A: 按照提示输入要测试的文件路径和目标目录。

### Q: 如何测试实际的为知笔记文件？

A: 使用 `test_attachment_simple.py` 或参考 `docs/test_guide.md` 中的手动测试步骤。

---

## 反馈

如果遇到问题或有改进建议，请提交 Issue 或 Pull Request。
