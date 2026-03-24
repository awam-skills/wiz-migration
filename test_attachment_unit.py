#!/usr/bin/env python3
"""
测试附件插入功能 - 单元测试版本

创建模拟数据测试 fix_asset_paths 功能
"""

import sys
import tempfile
import shutil
from pathlib import Path
import json

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

from logseq_migrator import fix_asset_paths


def create_test_data():
    """
    创建测试数据目录结构和文件
    """
    # 创建临时目录
    tmpdir = Path(tempfile.mkdtemp(prefix="wiz_test_"))
    print(f"创建测试目录: {tmpdir}")

    pages_dir = tmpdir / "pages"
    pages_dir.mkdir()

    # 创建一个深层目录结构的测试文件
    deep_dir = pages_dir / "a" / "b" / "c"
    deep_dir.mkdir(parents=True)

    # 创建带 _files 引用的 Markdown 文件
    md_with_files = deep_dir / "test_files.md"
    md_content_files = """# 测试文件

这是测试内容。

![图片1](test_files_files/image1.png)

![图片2](test_files_files/image2.jpg)

更多内容...
"""
    md_with_files.write_text(md_content_files, encoding='utf-8')

    # 创建带 _Attachments 引用的 Markdown 文件
    md_with_attachments = deep_dir / "test_attachments.md"
    md_content_attach = """# 测试附件

这里有附件引用。

![附件1](test_attachments_Attachments/attach1.pdf)
![附件2](test_attachments_Attachments/attach2.docx)

一些正文内容。
"""
    md_with_attachments.write_text(md_content_attach, encoding='utf-8')

    # 创建带混合引用的文件
    md_mixed = deep_dir / "test_mixed.md"
    md_content_mixed = """# 混合测试

包含两种类型的引用。

![file](test_mixed_files/file.png)
![attach](test_mixed_Attachments/attach.pdf)

结束。
"""
    md_mixed.write_text(md_content_mixed, encoding='utf-8')

    # 创建附件映射文件
    attachment_mapping = {
        'test_attachments': {
            'original_rel_path': 'a/b/c/test_attachments.md',
            'target_rel_path': 'a/b/c/test_attachments.md',
            'attach_dir_name': 'test_attachments_Attachments'
        },
        'test_mixed': {
            'original_rel_path': 'a/b/c/test_mixed.md',
            'target_rel_path': 'a/b/c/test_mixed.md',
            'attach_dir_name': 'test_mixed_Attachments'
        }
    }

    mapping_file = tmpdir / ".attachment_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(attachment_mapping, f, indent=2, ensure_ascii=False)

    return tmpdir, pages_dir, attachment_mapping


def run_test():
    """
    运行测试
    """
    print("=" * 80)
    print("附件插入功能单元测试")
    print("=" * 80)

    # 创建测试数据
    tmpdir, pages_dir, attachment_mapping = create_test_data()

    print(f"\npages 目录: {pages_dir}")

    # 显示原始内容
    print("\n" + "=" * 80)
    print("原始文件内容")
    print("=" * 80)

    for md_file in pages_dir.rglob("*.md"):
        print(f"\n📄 {md_file.relative_to(pages_dir)}:")
        print("-" * 60)
        content = md_file.read_text(encoding='utf-8')
        print(content)

    # 执行附件路径修复
    print("\n" + "=" * 80)
    print("执行附件路径修复")
    print("=" * 80)

    stats = fix_asset_paths(pages_dir, attachment_mapping)

    # 显示结果
    print("\n" + "=" * 80)
    print("修复结果")
    print("=" * 80)
    print(f"✅ 修复成功: {stats['fixed']} 处")
    print(f"📎 添加附件: {stats['attachments_added']} 个")

    if stats['failed'] > 0:
        print(f"❌ 修复失败: {stats['failed']} 处")
        for error in stats['errors']:
            print(f"   - {error}")

    # 显示修复后的内容
    print("\n" + "=" * 80)
    print("修复后文件内容")
    print("=" * 80)

    for md_file in pages_dir.rglob("*.md"):
        print(f"\n📄 {md_file.relative_to(pages_dir)}:")
        print("-" * 60)
        content = md_file.read_text(encoding='utf-8')
        print(content)

    # 验证结果
    print("\n" + "=" * 80)
    print("验证测试结果")
    print("=" * 80)

    test_results = []

    # 验证 test_files.md
    files_md = pages_dir / "a" / "b" / "c" / "test_files.md"
    files_content = files_md.read_text(encoding='utf-8')
    has_correct_path = "../../../../../assets/" in files_content or "../../../../assets/" in files_content
    has_attachments_section = "## 附件" in files_content

    test_results.append({
        'file': 'test_files.md',
        'has_correct_path': has_correct_path,
        'has_attachments_section': has_attachments_section,
        'passed': has_correct_path and not has_attachments_section
    })

    # 验证 test_attachments.md
    attach_md = pages_dir / "a" / "b" / "c" / "test_attachments.md"
    attach_content = attach_md.read_text(encoding='utf-8')
    has_removed_original = "_Attachments" not in attach_content or "attach1.pdf" not in attach_content or attach_content.count("attach1.pdf") == 1
    has_attachments_section = "## 附件" in attach_content
    has_correct_attach_path = "assets/attachments/test_attachments_Attachments/" in attach_content

    test_results.append({
        'file': 'test_attachments.md',
        'has_removed_original': has_removed_original,
        'has_attachments_section': has_attachments_section,
        'has_correct_attach_path': has_correct_attach_path,
        'passed': has_removed_original and has_attachments_section and has_correct_attach_path
    })

    # 验证 test_mixed.md
    mixed_md = pages_dir / "a" / "b" / "c" / "test_mixed.md"
    mixed_content = mixed_md.read_text(encoding='utf-8')
    has_files_path = "assets/" in mixed_content
    has_attachments_section = "## 附件" in mixed_content
    has_attach_path = "assets/attachments/test_mixed_Attachments/" in mixed_content

    test_results.append({
        'file': 'test_mixed.md',
        'has_files_path': has_files_path,
        'has_attachments_section': has_attachments_section,
        'has_attach_path': has_attach_path,
        'passed': has_files_path and has_attachments_section and has_attach_path
    })

    # 显示测试结果
    all_passed = True
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"\n{status}: {result['file']}")
        for key, value in result.items():
            if key != 'file' and key != 'passed':
                print(f"  {key}: {value}")
        if not result['passed']:
            all_passed = False

    # 清理
    print("\n" + "=" * 80)
    print(f"测试目录: {tmpdir}")
    cleanup = input("是否清理测试目录? (y/n): ").strip().lower()
    if cleanup == 'y':
        shutil.rmtree(tmpdir)
        print("✅ 已清理测试目录")
    else:
        print(f"测试目录保留: {tmpdir}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
