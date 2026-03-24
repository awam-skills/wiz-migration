#!/usr/bin/env python3
"""
测试附件添加功能
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from logseq_migrator import (
    _collect_attachments_from_dir,
    _parse_attach_dir_to_md_name,
    _find_md_file_for_attach_dir
)

# 测试目录
assets_dir = Path("G:/Data/knowledge/wiz-cb/assets")
pages_dir = Path("G:/Data/knowledge/wiz-cb/pages")

# 查找附件目录
attach_dir = assets_dir / "attachments" / "#学信网.txt#_Attachments"

print(f"附件目录: {attach_dir}")
print(f"目录是否存在: {attach_dir.exists()}")

if attach_dir.exists():
    # 收集文件
    files = _collect_attachments_from_dir(attach_dir)
    print(f"\n收集到的文件: {files}")

    # 解析 Markdown 文件名
    md_name = _parse_attach_dir_to_md_name(attach_dir.name)
    print(f"对应的 Markdown 文件: {md_name}")

    # 查找 Markdown 文件
    md_file = _find_md_file_for_attach_dir(attach_dir.name, pages_dir)
    print(f"找到的 Markdown 文件: {md_file}")

    if md_file:
        print(f"\nMarkdown 文件内容:")
        print(md_file.read_text(encoding='utf-8'))
