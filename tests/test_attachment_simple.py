#!/usr/bin/env python3
"""
简单的附件插入测试
"""

import sys
from pathlib import Path
import re

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

from logseq_migrator import fix_asset_paths


def test_single_file_with_path():
    """
    使用直接指定路径的方式测试
    """

    print("=" * 80)
    print("附件插入功能测试")
    print("=" * 80)

    # 用户输入路径
    print("\n请输入源 Markdown 文件路径:")
    print("示例: G:\\Data\\knowledge\\wiz\\10其他\\烂笔头\\01记录\\02学习\\学校学习")
    print("或者直接按回车使用默认路径")

    source_dir_input = input("路径: ").strip()

    if not source_dir_input:
        # 默认路径 - 需要手动输入完整路径
        print("\n请手动输入完整的源文件目录路径:")
        source_dir_input = input("> ").strip()

    if not source_dir_input:
        print("❌ 未指定路径，测试取消")
        return

    source_dir = Path(source_dir_input)

    if not source_dir.exists():
        print(f"❌ 目录不存在: {source_dir}")
        return

    # 查找包含"学信网"的文件
    print(f"\n在 {source_dir} 中查找文件...")
    md_files = list(source_dir.glob("*.md"))
    target_files = [f for f in md_files if "学信网" in f.name or "xinxin" in f.name.lower()]

    if not target_files:
        print("❌ 未找到包含'学信网'的文件")
        print(f"\n目录中的 .md 文件:")
        for f in md_files[:10]:  # 显示前10个
            print(f"  - {f.name}")
        return

    source_md = target_files[0]
    print(f"✅ 找到文件: {source_md.name}")

    # 读取并分析
    content = source_md.read_text(encoding='utf-8')

    print(f"\n文件信息:")
    print(f"  大小: {len(content)} 字符")
    print(f"  行数: {len(content.splitlines())} 行")

    # 查找附件引用
    pattern_files = r'!\[([^\]]*)\]\(([^\s\[]+)_files/([^)]+)\)'
    pattern_attach = r'!\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)'

    files_matches = re.findall(pattern_files, content)
    attach_matches = re.findall(pattern_attach, content)

    print(f"\n附件引用分析:")
    print(f"  _files 引用: {len(files_matches)}")
    for alt, note, file in files_matches[:5]:
        print(f"    - {file} (笔记: {note})")

    print(f"  _Attachments 引用: {len(attach_matches)}")
    attachment_files = []
    for alt, note, file in attach_matches:
        print(f"    - {file} (笔记: {note}, alt: {alt})")
        attachment_files.append(file)

    # 询问目标目录
    print("\n请输入目标 pages 目录:")
    print("示例: G:\\Data\\knowledge\\wiz-c\\pages")
    target_input = input("路径 (或按回车跳过): ").strip()

    if target_input:
        target_pages = Path(target_input)

        if not target_pages.exists():
            print(f"⚠️  目标目录不存在: {target_pages}")
            create = input("是否创建? (y/n): ").strip().lower()
            if create == 'y':
                target_pages.mkdir(parents=True, exist_ok=True)
                print(f"✅ 已创建目录")
            else:
                target_pages = None

        if target_pages:
            # 复制文件到目标
            target_file = target_pages / source_md.name
            target_file.parent.mkdir(parents=True, exist_ok=True)

            import shutil
            shutil.copy2(str(source_md), str(target_file))
            print(f"✅ 已复制到: {target_file}")

            # 查找附件映射
            mapping_file = target_pages.parent / ".attachment_mapping.json"
            attachment_mapping = {}

            if mapping_file.exists():
                import json
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    attachment_mapping = json.load(f)
                print(f"📋 加载附件映射: {len(attachment_mapping)} 条")

                # 显示当前笔记的映射
                note_name = source_md.stem
                if note_name in attachment_mapping:
                    info = attachment_mapping[note_name]
                    print(f"   附件目录: {info.get('attach_dir_name', 'N/A')}")

            # 询问是否执行修复
            run_fix = input("\n是否执行附件路径修复? (y/n): ").strip().lower()
            if run_fix == 'y':
                print("\n🔧 开始修复...")
                stats = fix_asset_paths(target_pages, attachment_mapping)

                print(f"\n修复结果:")
                print(f"  ✅ 修复: {stats['fixed']} 处")
                print(f"  📎 添加附件: {stats['attachments_added']} 个")

                if stats['failed'] > 0:
                    print(f"  ❌ 失败: {stats['failed']} 处")

                # 显示修复后的文件尾部
                print(f"\n修复后文件尾部内容 (最后 20 行):")
                fixed_content = target_file.read_text(encoding='utf-8')
                lines = fixed_content.splitlines()
                for line in lines[-20:]:
                    print(f"  {line}")

    # 生成测试报告
    print("\n" + "=" * 80)
    print("测试报告")
    print("=" * 80)
    print(f"源文件: {source_md}")
    print(f"文件名: {source_md.name}")
    print(f"笔记名 (stem): {source_md.stem}")
    print(f"\n发现的 _Attachments 文件: {len(attachment_files)}")
    for f in attachment_files:
        print(f"  - {f}")

    print("\n预期行为:")
    if attachment_files:
        print("  1. 移除 Markdown 中的 _Attachments 引用")
        print("  2. 在文件末尾添加附件区域")
        print("  3. 附件路径格式: ../assets/attachments/{笔记名}_Attachments/{文件名}")
        print(f"  4. 根据文件深度调整路径 (当前深度: {len(source_md.relative_to(source_dir.parent).parts) - 1})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_single_file_with_path()
