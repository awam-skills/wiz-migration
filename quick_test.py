#!/usr/bin/env python3
"""
快速验证脚本 - 测试附件插入功能
"""

import sys
import tempfile
from pathlib import Path
import json

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

# 导入函数
from logseq_migrator import fix_asset_paths
import re

print("=" * 80)
print("附件插入功能快速验证")
print("=" * 80)

# 创建临时测试目录
tmpdir = Path(tempfile.mkdtemp(prefix="wiz_attach_test_"))
pages_dir = tmpdir / "pages"
pages_dir.mkdir()

# 创建深层目录
deep_dir = pages_dir / "test" / "deep" / "path"
deep_dir.mkdir(parents=True)

# 测试文件1: 带 _Attachments 引用
test_md = deep_dir / "test_note.md"
test_md.write_text("""# 测试笔记

这是一篇测试笔记，包含附件引用。

![图片1](test_note_Attachments/image1.png)
![文档](test_note_Attachments/document.pdf)

正文内容结束。
""", encoding='utf-8')

# 创建附件映射
attachment_mapping = {
    'test_note': {
        'original_rel_path': 'test/deep/path/test_note.md',
        'target_rel_path': 'test/deep/path/test_note.md',
        'attach_dir_name': 'test_note_Attachments'
    }
}

print(f"\n测试目录: {pages_dir}")
print(f"测试文件: {test_md.relative_to(pages_dir)}")
print(f"相对深度: {len(test_md.relative_to(pages_dir).parts) - 1} 层")

print("\n原始内容:")
print("-" * 60)
print(test_md.read_text(encoding='utf-8'))

# 执行修复
print("\n执行 fix_asset_paths...")
stats = fix_asset_paths(pages_dir, attachment_mapping)

print(f"\n统计:")
print(f"  修复: {stats['fixed']}")
print(f"  添加附件: {stats['attachments_added']}")

# 读取修复后内容
fixed_content = test_md.read_text(encoding='utf-8')

print("\n修复后内容:")
print("=" * 80)
print(fixed_content)
print("=" * 80)

# 验证结果
print("\n验证结果:")
print("-" * 60)

# 检查是否移除了 _Attachments 引用
has_attachments_ref = "_Attachments/" in fixed_content
print(f"  ❌ 仍包含 _Attachments 引用: {has_attachments_ref}")

# 检查是否添加了附件区域
has_attachments_section = "\n\n## 附件\n\n" in fixed_content or "\n\n## 附件\n" in fixed_content
print(f"  ✅ 包含附件区域: {has_attachments_section}")

# 检查附件路径是否正确
# 深度是 3 (test/deep/path/file.md -> parts = 4, depth = 3)
# 期望路径: ../../../../../assets/attachments/test_note_Attachments/
expected_path_prefix = "../" * 4 + "assets/attachments/test_note_Attachments/"
has_correct_path = expected_path_prefix in fixed_content
print(f"  ✅ 包含正确的相对路径: {has_correct_path}")
print(f"     期望: {expected_path_prefix}")

# 检查附件列表中的文件
has_image1 = "image1.png" in fixed_content
has_document = "document.pdf" in fixed_content
print(f"  ✅ 包含 image1.png: {has_image1}")
print(f"  ✅ 包含 document.pdf: {has_document}")

# 总体结果
if has_attachments_section and has_correct_path and has_image1 and has_document and not has_attachments_ref:
    print("\n✅ 所有验证通过！")
else:
    print("\n❌ 部分验证失败")

# 清理
import shutil
shutil.rmtree(tmpdir)
print(f"\n已清理测试目录: {tmpdir}")

print("=" * 80)
