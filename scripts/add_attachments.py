"""
为知笔记迁移 - _Attachments 添加工具

根据用户的最新需求：
1. 不依赖第一阶段的 attachment_mapping.json
2. 从 assets\attachments 获取目录名和里面文件
3. 通过目录名解析出对应的 Markdown 文件名（"assets\attachments\#学信网.txt#_Attachments" -> #学信网.txt#.md）
4. 生成 Markdown 时，只要是名称匹配的 Markdown，就在它的后面添加上附件区域
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def parse_attach_dir_to_md_name(attach_dir_name: str) -> str:
    """
    从附件目录名解析出对应的 Markdown 文件名

    例如：
    "#学信网.txt#_Attachments" -> "#学信网.txt#.md"
    "笔记名_Attachments" -> "笔记名.md"

    Args:
        attach_dir_name: 附件目录名（如 "笔记名_Attachments"）

    Returns:
        Markdown 文件名（如 "笔记名.md"）
    """
    # 移除 _Attachments 后缀
    if attach_dir_name.endswith("_Attachments"):
        md_name = attach_dir_name[:-12]  # "_Attachments" 长度为 12
    else:
        md_name = attach_dir_name

    # 添加 .md 扩展名
    return md_name + ".md"


def find_md_file_for_attach_dir(attach_dir_name: str, pages_dir: Path) -> Path:
    """
    在 pages 目录中查找与附件目录名匹配的 Markdown 文件

    Args:
        attach_dir_name: 附件目录名
        pages_dir: pages 目录路径

    Returns:
        匹配的 Markdown 文件路径，如果找不到返回 None
    """
    md_name = parse_attach_dir_to_md_name(attach_dir_name)

    # 递归搜索所有 md 文件
    for md_file in pages_dir.rglob("*.md"):
        if md_file.name == md_name:
            return md_file

    return None


def collect_attachments_from_dir(attach_dir: Path) -> List[str]:
    """
    收集附件目录中的所有文件

    Args:
        attach_dir: 附件目录路径

    Returns:
        文件名列表（使用 / 作为路径分隔符）
    """
    files = []
    for item in attach_dir.rglob("*"):
        if item.is_file():
            # 保存相对路径（相对于附件目录），使用 / 作为分隔符
            rel_path = item.relative_to(attach_dir)
            # 转换为使用 / 的路径（Markdown 需要）
            files.append(str(rel_path).replace('\\', '/'))
    return sorted(files)



def add_attachment_section_to_md(md_file: Path, attach_files: List[str], assets_dir_name: str) -> bool:
    """
    在 Markdown 文件中添加附件区域

    Args:
        md_file: Markdown 文件路径
        attach_files: 附件文件列表
        assets_dir_name: assets 目录下附件目录的名称

    Returns:
        是否成功添加（如果文件已存在附件区域则跳过）
    """
    content = md_file.read_text(encoding='utf-8')

    # 计算相对路径
    rel_path = md_file.relative_to(md_file.parents[-1])  # pages 目录
    depth = len(rel_path.parts) - 1  # 减1是因为 rel_path 包含文件名

    # 生成正确数量的 "../" 前缀
    if depth > 0:
        assets_prefix = "../" * (depth + 1)  # +1 是因为要跳出 pages/ 目录
    else:
        assets_prefix = "../"

    # 构建附件区域
    attachment_section = "\n\n---\n\n## 附件\n\n"
    for file_name in attach_files:
        attachment_path = f"{assets_prefix}assets/attachments/{assets_dir_name}/{file_name}"
        attachment_section += f"[{file_name}]({attachment_path})\n\n"


    # 检查是否已有附件区域
    if "## 附件" in content:
        # 查找附件区域的开始位置
        attach_match = re.search(r'\n\n## 附件\n', content)
        if attach_match:
            # 从附件区域开始截取，移除旧内容
            content = content[:attach_match.start()]
            # 添加新的附件区域
            content += attachment_section
            md_file.write_text(content, encoding='utf-8')
            return True
        return False
    else:
        # 追加附件区域
        md_file.write_text(content + attachment_section, encoding='utf-8')
        return True



def add_attachments_to_markdown(
    pages_dir: Path,
    assets_dir: Path,
    assets_attachments_subdir: str = "attachments"
) -> Dict:
    """
    为 Markdown 文件添加 _Attachments 引用

    根据新策略：
    1. 扫描 assets/attachments 目录下的所有子目录
    2. 对每个子目录（如 "笔记名_Attachments"），解析出对应的 Markdown 文件名
    3. 在 pages 目录中查找匹配的 Markdown 文件
    4. 收集附件目录中的所有文件
    5. 在 Markdown 文件尾部添加附件区域

    Args:
        pages_dir: Logseq pages 目录
        assets_dir: Logseq assets 目录
        assets_attachments_subdir: assets 目录下的附件子目录名（默认为 "attachments"）

    Returns:
        统计信息
    """
    stats = {
        "processed": 0,
        "not_found": 0,
        "added": 0,
        "skipped": 0,
        "failed": 0,
        "errors": []
    }

    assets_attach_dir = assets_dir / assets_attachments_subdir

    if not assets_attach_dir.exists():
        stats["errors"].append(f"附件目录不存在: {assets_attach_dir}")
        return stats

    # 查找所有子目录（排除自身）
    attach_dirs = [d for d in assets_attach_dir.iterdir() if d.is_dir()]

    if not attach_dirs:
        stats["errors"].append(f"未找到任何附件子目录")
        return stats

    print(f"找到 {len(attach_dirs)} 个附件目录待处理")

    for attach_dir in attach_dirs:
        stats["processed"] += 1

        print(f"\n处理附件目录: {attach_dir.name}")

        # 解析对应的 Markdown 文件名
        md_name = parse_attach_dir_to_md_name(attach_dir.name)
        print(f"  对应的 Markdown 文件: {md_name}")

        # 在 pages 目录中查找匹配的文件
        md_file = find_md_file_for_attach_dir(attach_dir.name, pages_dir)

        if md_file is None:
            print(f"  ⚠️  未找到对应的 Markdown 文件")
            stats["not_found"] += 1
            continue

        print(f"  ✅ 找到 Markdown 文件: {md_file.relative_to(pages_dir)}")

        # 收集附件文件
        attach_files = collect_attachments_from_dir(attach_dir)
        print(f"  📁 找到 {len(attach_files)} 个附件文件")

        if not attach_files:
            print(f"  ⏭️  目录为空，跳过")
            stats["skipped"] += 1
            continue

        # 添加附件区域
        try:
            result = add_attachment_section_to_md(md_file, attach_files, attach_dir.name)
            if result:
                print(f"  ✅ 已添加附件区域（{len(attach_files)} 个文件）")
                stats["added"] += len(attach_files)
            else:
                print(f"  ⏭️  附件区域已存在，已更新")
                stats["skipped"] += 1
        except Exception as e:
            print(f"  ❌ 添加失败: {e}")
            stats["failed"] += 1
            stats["errors"].append(f"{md_file.name}: {e}")

    return stats


def print_summary(stats: Dict):
    """打印统计摘要"""
    print("\n" + "=" * 60)
    print("附件区域添加完成!")
    print("=" * 60)
    print(f"  📂 处理的附件目录: {stats['processed']} 个")
    print(f"  ✅ 成功添加引用的文件: {stats['added']} 个")
    if stats['skipped'] > 0:
        print(f"  ⏭️  跳过: {stats['skipped']} 个")
    if stats['not_found'] > 0:
        print(f"  ⚠️  未找到对应 Markdown 文件: {stats['not_found']} 个")
    if stats['failed'] > 0:
        print(f"  ❌ 失败: {stats['failed']} 个")

    if stats['errors']:
        print("\n错误详情:")
        for error in stats['errors']:
            print(f"  - {error}")

    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python add_attachments.py <pages_dir> <assets_dir> [attachments_subdir]")
        print("示例:")
        print("  python add_attachments.py G:/Data/knowledge/wiz-c/pages G:/Data/knowledge/wiz-c/assets")
        print("  python add_attachments.py G:/Data/knowledge/wiz-c/pages G:/Data/knowledge/wiz-c/assets attachments")
        sys.exit(1)

    pages_dir = Path(sys.argv[1]).resolve()
    assets_dir = Path(sys.argv[2]).resolve()
    attachments_subdir = sys.argv[3] if len(sys.argv) > 3 else "attachments"

    if not pages_dir.exists():
        print(f"错误: pages 目录不存在: {pages_dir}")
        sys.exit(1)

    if not assets_dir.exists():
        print(f"错误: assets 目录不存在: {assets_dir}")
        sys.exit(1)

    print(f"Pages 目录: {pages_dir}")
    print(f"Assets 目录: {assets_dir}")
    print(f"Attachments 子目录: {attachments_subdir}")

    stats = add_attachments_to_markdown(pages_dir, assets_dir, attachments_subdir)
    print_summary(stats)
