#!/usr/bin/env python3
"""
测试 Markdown 插入附件功能

该脚本用于测试从原始 wiz 目录重新生成 Markdown 到目标目录，
并验证附件是否正确插入到 Markdown 文件尾部。
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

from logseq_migrator import fix_asset_paths


def test_attachment_insertion():
    """
    测试附件插入功能

    测试步骤:
    1. 指定原始 Markdown 文件路径
    2. 指定目标 pages 目录
    3. 模拟运行 fix_asset_paths，检查附件是否正确插入
    """

    # 配置测试路径
    # 注意：路径中的 # 符号在 Windows 中是有效的文件名
    source_md = Path(r"G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习").resolve()
    # 由于 # 是特殊字符，使用 glob 查找
    source_files = list(source_md.glob("*学信网*"))
    source_md = source_files[0] if source_files else None

    target_pages = Path(r"G:\Data\knowledge\wiz-c\pages")

    # 检查源文件是否存在
    if not source_md.exists():
        print(f"❌ 源文件不存在: {source_md}")
        return False

    print("=" * 80)
    print("测试附件插入功能")
    print("=" * 80)
    print(f"源文件: {source_md}")
    print(f"目标 pages 目录: {target_pages}")
    print()

    # 读取原始文件内容
    print("📄 读取源文件内容...")
    original_content = source_md.read_text(encoding='utf-8')

    # 显示文件统计信息
    print(f"   文件大小: {len(original_content)} 字符")
    print(f"   文件行数: {len(original_content.splitlines())} 行")

    # 查找附件引用
    import re

    # 查找 _files 引用
    pattern_files = re.compile(r'!\[([^\]]*)\]\(([^\s\[]+)_files/([^)]+)\)')
    files_matches = pattern_files.findall(original_content)
    print(f"\n📎 找到 _files 引用: {len(files_matches)} 个")
    for match in files_matches:
        print(f"   - {match[0]} : {match[1]}_files/{match[2]}")

    # 查找 _Attachments 引用
    pattern_attach = re.compile(r'!\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)')
    attach_matches = pattern_attach.findall(original_content)
    print(f"\n📎 找到 _Attachments 引用: {len(attach_matches)} 个")
    for match in attach_matches:
        print(f"   - {match[0]} : {match[1]}_Attachments/{match[2]}")

    # 检查目标目录是否存在
    if not target_pages.exists():
        print(f"\n⚠️  目标目录不存在: {target_pages}")
        print("是否需要创建目标目录结构？")
        create_target = input("输入 'y' 创建目录结构，其他键跳过: ").strip().lower()

        if create_target == 'y':
            # 创建目标文件路径
            target_file = target_pages / source_md.name
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # 复制源文件到目标
            import shutil
            shutil.copy2(str(source_md), str(target_file))
            print(f"✅ 已复制文件到: {target_file}")
        else:
            print("❌ 测试取消")
            return False

    print("\n" + "=" * 80)
    print("准备运行附件路径修复...")
    print("=" * 80)

    # 查找附件映射文件
    mapping_file = target_pages.parent / ".attachment_mapping.json"
    attachment_mapping = {}

    if mapping_file.exists():
        import json
        with open(mapping_file, 'r', encoding='utf-8') as f:
            attachment_mapping = json.load(f)
        print(f"📋 加载附件映射: {mapping_file}")
        print(f"   映射数量: {len(attachment_mapping)}")

        # 显示当前笔记的映射信息
        note_name = source_md.stem
        if note_name in attachment_mapping:
            info = attachment_mapping[note_name]
            print(f"   当前笔记 '{note_name}' 的映射:")
            print(f"     - 原始相对路径: {info.get('original_rel_path', 'N/A')}")
            print(f"     - 目标相对路径: {info.get('target_rel_path', 'N/A')}")
            print(f"     - 附件目录名: {info.get('attach_dir_name', 'N/A')}")
    else:
        print("⚠️  未找到附件映射文件: " + str(mapping_file))

    # 确认是否执行
    confirm = input("\n是否执行附件路径修复？(y/n): ").strip().lower()

    if confirm != 'y':
        print("❌ 操作已取消")
        return False

    # 执行附件路径修复
    print("\n🔧 开始修复附件路径...")
    stats = fix_asset_paths(target_pages, attachment_mapping)

    print("\n" + "=" * 80)
    print("修复结果")
    print("=" * 80)
    print(f"✅ 修复成功: {stats['fixed']} 处")
    print(f"📎 添加附件: {stats['attachments_added']} 个")

    if stats['failed'] > 0:
        print(f"❌ 修复失败: {stats['failed']} 处")
        print(f"错误信息:")
        for error in stats['errors']:
            print(f"   - {error}")

    # 显示修复后的文件内容预览
    target_file = target_pages / source_md.name
    if target_file.exists():
        fixed_content = target_file.read_text(encoding='utf-8')

        print("\n" + "=" * 80)
        print("修复后的文件预览 (最后 30 行)")
        print("=" * 80)
        lines = fixed_content.splitlines()
        for line in lines[-30:]:
            print(line)

        # 检查是否包含附件区域
        if "\n\n## 附件\n\n" in fixed_content:
            print("\n✅ 成功添加附件区域")
        else:
            print("\n⚠️  未找到附件区域")

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)

    return True


def test_single_file():
    """
    测试单个文件的附件插入（简化版）
    """
    # 配置路径
    # 注意：路径中的 # 符号在 Windows 中是有效的文件名
    source_base = Path(r"G:\Data\knowledge\wiz\10其他\烂笔头\01记录\02学习\学校学习").resolve()
    source_files = list(source_base.glob("*学信网*"))
    source_md = source_files[0] if source_files else None
    target_pages = Path(r"G:\Data\knowledge\wiz-c\pages")

    print("简化测试模式")

    # 检查源文件
    if not source_md or not source_md.exists():
        print(f"❌ 源文件不存在")
        return

    print(f"源文件: {source_md}")
    print(f"目标目录: {target_pages}")

    # 读取并分析
    content = source_md.read_text(encoding='utf-8')

    import re

    # 查找所有附件引用
    all_attachments = []

    pattern_files = r'!\[([^\]]*)\]\(([^\s\[]+)_files/([^)]+)\)'
    pattern_attach = r'!\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)'

    files_matches = re.findall(pattern_files, content)
    attach_matches = re.findall(pattern_attach, content)

    print(f"\n分析结果:")
    print(f"  _files 引用: {len(files_matches)}")
    print(f"  _Attachments 引用: {len(attach_matches)}")

    if attach_matches:
        print(f"\n_Attachments 文件列表:")
        for alt, note, file in attach_matches:
            print(f"  - {file} (笔记: {note}, alt: {alt})")

    # 如果目标文件存在，显示当前内容
    target_file = target_pages / source_md.name
    if target_file.exists():
        target_content = target_file.read_text(encoding='utf-8')
        print(f"\n目标文件存在，行数: {len(target_content.splitlines())}")

        if "## 附件" in target_content:
            print("✅ 包含附件区域")
            # 显示附件区域
            lines = target_content.splitlines()
            start_idx = None
            for i, line in enumerate(lines):
                if "## 附件" in line:
                    start_idx = i
                    break

            if start_idx:
                print("\n附件区域内容:")
                for line in lines[start_idx:start_idx+15]:
                    print(f"  {line}")
        else:
            print("⚠️  不包含附件区域")


if __name__ == "__main__":
    print("选择测试模式:")
    print("1. 完整测试 (包含复制和修复)")
    print("2. 简化测试 (仅分析文件)")

    choice = input("请输入选择 (1/2): ").strip()

    if choice == "1":
        test_attachment_insertion()
    elif choice == "2":
        test_single_file()
    else:
        print("无效选择")
