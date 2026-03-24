#!/usr/bin/env python3
"""
Logseq 迁移模块
将 Markdown 文件和附件迁移到 Logseq 图谱
"""

import os
import re
import shutil
import hashlib
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# 文件存在策略: None=未选择, 'overwrite'=覆盖, 'skip'=跳过
_file_exists_strategy: Optional[str] = None


def calculate_md5(file_path: Path) -> str:
    """计算文件的 MD5 值"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def ask_file_exists_strategy() -> str:
    """询问用户文件存在时的处理策略（仅第一次询问）"""
    global _file_exists_strategy

    if _file_exists_strategy is not None:
        return _file_exists_strategy

    print("\n" + "=" * 60)
    print("⚠️  检测到目标文件已存在")
    print("=" * 60)
    print("请选择处理策略（本次迁移全程有效）:")
    print("  1. 覆盖 (overwrite) - 替换已有文件")
    print("  2. 跳过 (skip) - 保留已有文件，不处理")
    print("  3. 重命名 (rename) - 自动重命名新文件（添加序号）")

    while True:
        choice = input("\n请输入选择 (1/2/3): ").strip()
        if choice == '1':
            _file_exists_strategy = 'overwrite'
            print("✅ 已选择: 覆盖已有文件")
            break
        elif choice == '2':
            _file_exists_strategy = 'skip'
            print("⏭️  已选择: 跳过已有文件")
            break
        elif choice == '3':
            _file_exists_strategy = 'rename'
            print("📝 已选择: 自动重命名")
            break
        else:
            print("无效选择，请输入 1、2 或 3")

    return _file_exists_strategy


def handle_file_exists(src_file: Path, dest_file: Path, strategy: str) -> bool:
    """根据策略处理已存在的文件

    Args:
        src_file: 源文件
        dest_file: 目标文件
        strategy: 'overwrite' | 'skip' | 'rename'

    Returns:
        bool: 是否需要执行操作（True=需要复制/移动, False=跳过）
    """
    if strategy == 'skip':
        return False
    elif strategy == 'overwrite':
        return True
    elif strategy == 'rename':
        # 先检查 MD5 是否一致
        try:
            src_md5 = calculate_md5(src_file)
            dest_md5 = calculate_md5(dest_file)
            if src_md5 == dest_md5:
                print(f"    ⏭️  内容一致，跳过: {dest_file.name} (MD5: {src_md5[:8]}...)")
                return False  # 内容一致，不需要复制
        except Exception as e:
            print(f"    ⚠️  MD5 检查失败: {e}，将执行重命名")

        # 重命名目标文件
        base = dest_file.stem
        ext = dest_file.suffix
        counter = 1
        while dest_file.exists():
            dest_file = dest_file.parent / f"{base}_{counter}{ext}"
            counter += 1
        return True
    else:
        return False


def run_logseq_migration(
    markdown_dir: str,
    graph_dir: str,
    move_to_subdir: str = None
) -> Dict:
    """
    运行 Logseq 迁移

    Args:
        markdown_dir: Markdown 文件所在目录（通常是阶段2的输出目录）
        graph_dir: Logseq 图谱根目录
        move_to_subdir: 可选，子目录名（如原笔记本分类），用于组织 pages 下的文件

    Returns:
        dict: 迁移结果统计
    """
    md_dir = Path(markdown_dir).resolve()
    graph = Path(graph_dir).resolve()

    if not md_dir.exists():
        return {"success": False, "error": f"Markdown 目录不存在: {md_dir}"}

    if not graph.exists():
        return {"success": False, "error": f"图谱目录不存在: {graph}"}

    results = {
        "success": True,
        "attachments_copied": 0,
        "attachments_skipped": 0,
        "attachments_failed": 0,
        "md_files_copied": 0,
        "md_files_skipped": 0,
        "md_files_failed": 0,
        "paths_fixed": 0,
        "paths_failed": 0,
        "errors": []
    }

    # 确定 pages 和 assets 目录
    pages_dir = graph / "pages"
    assets_dir = graph / "assets"

    print(f"\n📁 Markdown 源目录: {md_dir}")
    print(f"📁 Logseq 图谱目录: {graph}")
    print(f"📁 Pages 目录: {pages_dir}")
    print(f"📁 Assets 目录: {assets_dir}")

    # 步骤1: 收集并复制附件到 assets/
    print("\n" + "=" * 60)
    print("步骤 1: 收集附件到 assets/")
    print("=" * 60)

    attach_result = collect_attachments_to_assets(md_dir, assets_dir)
    results["attachments_copied"] = attach_result["copied"]
    results["attachments_skipped"] = attach_result["skipped"]
    results["attachments_failed"] = attach_result["failed"]

    # 步骤2: 移动 Markdown 文件到 pages/
    print("\n" + "=" * 60)
    print("步骤 2: 移动 Markdown 文件到 pages/")
    print("=" * 60)

    target_pages_dir = pages_dir
    if move_to_subdir:
        target_pages_dir = pages_dir / move_to_subdir

    md_result = move_markdown_to_pages(md_dir, target_pages_dir)
    results["md_files_copied"] = md_result["copied"]
    results["md_files_skipped"] = md_result.get("skipped", 0)
    results["md_files_failed"] = md_result["failed"]

    # 步骤3: 批量替换附件路径
    print("\n" + "=" * 60)
    print("步骤 3: 修复附件路径")
    print("=" * 60)

    # 修复 pages 目录下的所有 md 文件
    path_result = fix_asset_paths(pages_dir)
    results["paths_fixed"] = path_result["fixed"]
    results["paths_failed"] = path_result["failed"]

    # 如果有子目录，也需要处理
    if move_to_subdir and (pages_dir / move_to_subdir).exists():
        path_result2 = fix_asset_paths(pages_dir / move_to_subdir)
        results["paths_fixed"] += path_result2["fixed"]
        results["paths_failed"] += path_result2["failed"]

    # 输出总结
    print("\n" + "=" * 60)
    print("迁移完成!")
    print("=" * 60)
    print(f"  ✅ 附件已复制到 assets/: {results['attachments_copied']} 个")
    if results['attachments_skipped'] > 0:
        print(f"  ⏭️  附件已存在跳过: {results['attachments_skipped']} 个")
    if results['attachments_failed'] > 0:
        print(f"  ❌ 附件复制失败: {results['attachments_failed']} 个")
    print(f"  ✅ Markdown 文件已复制: {results['md_files_copied']} 个")
    if results.get('md_files_skipped', 0) > 0:
        print(f"  ⏭️  Markdown 文件已存在跳过: {results['md_files_skipped']} 个")
    if results['md_files_failed'] > 0:
        print(f"  ❌ Markdown 移动失败: {results['md_files_failed']} 个")
    print(f"  ✅ 路径已修复: {results['paths_fixed']} 处")
    if results['paths_failed'] > 0:
        print(f"  ❌ 路径修复失败: {results['paths_failed']} 处")

    return results


def collect_attachments_to_assets(
    source_dir: Path,
    assets_dir: Path
) -> Dict:
    """
    收集源目录下的所有附件文件夹，复制到 assets/

    根据附件类型区分处理：
    - _files: 这些原本在 Markdown 中就已经存在，直接放在 assets 目录首层
    - _Attachments: 这些文件在原 Markdown 中不存在，放在 assets/attachments 目录下

    Args:
        source_dir: 包含 Markdown 文件和附件的源目录
        assets_dir: Logseq 的 assets/ 目录

    Returns:
        dict: 统计信息
    """
    stats = {"copied": 0, "skipped": 0, "failed": 0, "errors": []}

    # 确保 assets 目录存在
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 分别查找 _files 和 _Attachments 目录
    files_dirs = []
    attachments_dirs = []
    for root, dirs, files in os.walk(source_dir):
        for d in dirs:
            if d.endswith("_files"):
                files_dirs.append(Path(root) / d)
            elif d.endswith("_Attachments"):
                attachments_dirs.append(Path(root) / d)

    print(f"找到 {len(files_dirs)} 个 _files 目录（直接放在 assets 首层）")
    print(f"找到 {len(attachments_dirs)} 个 _Attachments 目录（放在 assets/attachments）")

    # 处理 _files 目录（直接放在 assets 首层）
    for idx, files_dir in enumerate(files_dirs, 1):
        print(f"\n[{idx}/{len(files_dirs)}] 处理 _files: {files_dir.name}")

        try:
            file_count = 0
            for item in files_dir.rglob("*"):
                if item.is_file():
                    # _files 类型：直接放在 assets 首层
                    dest_file = assets_dir / item.name

                    # 处理同名文件
                    if dest_file.exists():
                        # 先检查 MD5 是否一致（无论策略如何）
                        try:
                            src_md5 = calculate_md5(item)
                            dest_md5 = calculate_md5(dest_file)
                            if src_md5 == dest_md5:
                                print(f"    ⏭️  内容一致，跳过: {item.name}")
                                stats["skipped"] += 1
                                continue
                        except Exception:
                            pass  # MD5 检查失败，继续使用策略处理

                        # MD5 不一致，按策略处理
                        strategy = ask_file_exists_strategy()

                        if strategy == 'skip':
                            print(f"    ⏭️  跳过: {item.name}")
                            stats["skipped"] += 1
                            continue

                        elif strategy == 'rename':
                            # 重命名目标文件
                            base = dest_file.stem
                            ext = dest_file.suffix
                            counter = 1
                            while dest_file.exists():
                                dest_file = dest_file.parent / f"{base}_{counter}{ext}"
                                counter += 1
                            print(f"    ⚠️  重命名: {dest_file.name}")

                        elif strategy == 'overwrite':
                            print(f"    ⚠️  覆盖: {item.name}")

                    # 执行复制/覆盖
                    shutil.copy2(item, dest_file)
                    file_count += 1

            stats["copied"] += file_count
            print(f"    ✅ 复制完成 ({file_count} 个文件) -> assets/")

        except Exception as e:
            print(f"    ❌ 复制失败: {e}")
            stats["failed"] += 1
            stats["errors"].append(str(e))

    # 处理 _Attachments 目录（放在 assets/attachments 目录下）
    for idx, attach_dir in enumerate(attachments_dirs, 1):
        print(f"\n[{idx}/{len(attachments_dirs)}] 处理 _Attachments: {attach_dir.name}")

        try:
            file_count = 0
            for item in attach_dir.rglob("*"):
                if item.is_file():
                    # _Attachments 类型：放在 assets/attachments 目录下
                    attach_subdir = assets_dir / "attachments" / attach_dir.name
                    attach_subdir.mkdir(parents=True, exist_ok=True)
                    dest_file = attach_subdir / item.name

                    # 处理同名文件
                    if dest_file.exists():
                        # 先检查 MD5 是否一致（无论策略如何）
                        try:
                            src_md5 = calculate_md5(item)
                            dest_md5 = calculate_md5(dest_file)
                            if src_md5 == dest_md5:
                                print(f"    ⏭️  内容一致，跳过: {attach_dir.name}/{item.name}")
                                stats["skipped"] += 1
                                continue
                        except Exception:
                            pass  # MD5 检查失败，继续使用策略处理

                        # MD5 不一致，按策略处理
                        strategy = ask_file_exists_strategy()

                        if strategy == 'skip':
                            print(f"    ⏭️  跳过: {attach_dir.name}/{item.name}")
                            stats["skipped"] += 1
                            continue

                        elif strategy == 'rename':
                            # 重命名目标文件
                            base = dest_file.stem
                            ext = dest_file.suffix
                            counter = 1
                            while dest_file.exists():
                                dest_file = dest_file.parent / f"{base}_{counter}{ext}"
                                counter += 1
                            print(f"    ⚠️  重命名: {dest_file.name}")

                        elif strategy == 'overwrite':
                            print(f"    ⚠️  覆盖: {attach_dir.name}/{item.name}")

                    # 执行复制/覆盖
                    shutil.copy2(item, dest_file)
                    file_count += 1

            stats["copied"] += file_count
            print(f"    ✅ 复制完成 ({file_count} 个文件) -> assets/attachments/{attach_dir.name}/")

        except Exception as e:
            print(f"    ❌ 复制失败: {e}")
            stats["failed"] += 1
            stats["errors"].append(str(e))

    return stats


def move_markdown_to_pages(
    source_dir: Path,
    pages_dir: Path
) -> Dict:
    """
    将 Markdown 文件复制到 Logseq pages/ 目录，保持原目录结构（保留原文件）

    Args:
        source_dir: Markdown 文件所在目录
        pages_dir: Logseq 的 pages/ 目录

    Returns:
        dict: 统计信息
    """
    stats = {"copied": 0, "failed": 0, "skipped": 0, "errors": []}

    # 确保 pages 目录存在
    pages_dir.mkdir(parents=True, exist_ok=True)

    # 递归查找所有 .md 文件，保持原目录结构
    md_files = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.endswith(".md"):
                md_files.append(Path(root) / f)

    print(f"找到 {len(md_files)} 个 Markdown 文件")

    if not md_files:
        print("⚠️  未找到 Markdown 文件")
        return stats

    # 用于检测同名已存在的文件（用于MD5比对）
    for md_file in md_files:
        try:
            # 计算相对于 source_dir 的路径，保持原目录结构
            rel_path = md_file.relative_to(source_dir)
            dest_file = pages_dir / rel_path  # 使用完整相对路径

            # 确保目标目录存在
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # 处理同名文件
            if dest_file.exists():
                # 先检查 MD5 是否一致
                try:
                    src_md5 = calculate_md5(md_file)
                    dest_md5 = calculate_md5(dest_file)
                    if src_md5 == dest_md5:
                        print(f"    ⏭️  内容一致，跳过: {rel_path} (MD5: {src_md5[:8]}...)")
                        stats["skipped"] += 1
                        continue
                except Exception:
                    pass  # MD5 检查失败，继续使用策略处理

                strategy = ask_file_exists_strategy()
                if strategy == 'skip':
                    print(f"    ⏭️  跳过: {rel_path}（已存在）")
                    stats["skipped"] += 1
                    continue
                elif strategy == 'rename':
                    # 重命名目标文件
                    base = dest_file.stem
                    ext = dest_file.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = dest_file.parent / f"{base}_{counter}{ext}"
                        counter += 1
                    print(f"    ⚠️  重命名: {dest_file.name}")
                elif strategy == 'overwrite':
                    print(f"    ⚠️  覆盖: {rel_path}")

            # 复制而不是移动，保留原文件
            shutil.copy2(str(md_file), str(dest_file))
            stats["copied"] += 1
            print(f"    ✅ 复制: {rel_path} -> pages/")

        except Exception as e:
            print(f"    ❌ 复制失败 {md_file.name}: {e}")
            stats["failed"] += 1
            stats["errors"].append(str(e))

    return stats


def fix_asset_paths(pages_dir: Path) -> Dict:
    """
    批量修复 Markdown 文件中的附件路径

    根据附件类型使用不同路径：
    - _files: 原在 Markdown 中存在，替换为 ../assets/文件名
    - _Attachments: 原不在 Markdown 中，替换为 ../assets/attachments/目录名/文件名
             并在 Markdown 尾部添加附件区域引用

    Args:
        pages_dir: Logseq pages/ 目录

    Returns:
        dict: 统计信息
    """
    stats = {"fixed": 0, "failed": 0, "errors": [], "attachments_added": 0}

    # 查找所有 md 文件
    md_files = list(pages_dir.rglob("*.md"))

    print(f"找到 {len(md_files)} 个 Markdown 文件待处理")

    for md_file in md_files:
        try:
            # 计算从 md 文件到 pages 目录的相对深度，用于生成正确的 assets 路径
            rel_path = md_file.relative_to(pages_dir)
            depth = len(rel_path.parts) - 1  # 减1是因为 rel_path 包含文件名
            # 生成正确数量的 "../" 前缀
            if depth > 0:
                assets_prefix = "../" * (depth + 1)  # +1 是因为要跳出 pages/ 目录
            else:
                assets_prefix = "../"

            content = md_file.read_text(encoding='utf-8')
            original_content = content

            # 收集 _Attachments 引用（需要在尾部添加附件区域）
            attachments_to_add = []

            # 处理 _files 格式
            # 原: ![xxx](笔记名_files/abc.png)
            # 替: ![xxx](../assets/abc.png) 或 ../../assets/abc.png 等，取决于 md 文件的深度
            pattern_files = re.compile(r'(!?)\[([^\]]*)\]\(([^\s\[]+)_files/([^)]+)\)')
            matches_files = pattern_files.findall(content)
            if matches_files:
                for prefix, alt_text, note_name, file_name in matches_files:
                    old_pattern = f"{prefix}[{alt_text}]({note_name}_files/{file_name})"
                    # 保留原始的 alt text，如果为空则使用文件名
                    display_text = alt_text if alt_text else file_name
                    new_pattern = f"{prefix}[{display_text}]({assets_prefix}assets/{file_name})"
                    content = content.replace(old_pattern, new_pattern)
                stats["fixed"] += len(matches_files)

            # 处理 _Attachments 格式
            # 原: ![xxx](笔记名_Attachments/abc.png)
            # 替: 在文档内移除（将在尾部统一添加）
            pattern_attach = re.compile(r'(!?)\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)')
            matches_attach = pattern_attach.findall(content)
            if matches_attach:
                for prefix, alt_text, note_name, file_name in matches_attach:
                    old_pattern = f"{prefix}[{alt_text}]({note_name}_Attachments/{file_name})"
                    # 记录到待添加的附件列表
                    attachments_to_add.append(file_name)
                    # 从原文档中移除这个引用
                    content = content.replace(old_pattern, '')
                    # 同时移除可能的单独行
                    content = re.sub(r'^\s*$', '\n', content)
                stats["fixed"] += len(matches_attach)

            # 如果有 _Attachments 引用，在文档尾部添加附件区域
            if attachments_to_add:
                # 获取笔记名（去除路径和扩展名）
                note_name = md_file.stem

                # 添加附件区域标记
                attachment_section = "\n\n---\n\n## 附件\n\n"
                for file_name in attachments_to_add:
                    # 构建正确的路径：../assets/attachments/笔记名_Attachments/文件名
                    attachment_dir = f"{note_name}_Attachments"
                    attachment_path = f"../assets/attachments/{attachment_dir}/{file_name}"
                    attachment_section += f"![{file_name}]({attachment_path})\n\n"

                # 如果文档已有附件区域，替换；否则追加
                if "\n\n## 附件\n" in content:
                    # 替换已有的附件区域
                    content = re.sub(r'\n\n## 附件\n\n.*?(?=\n\n## |\n\n---\n\n$|$)',
                                    attachment_section.strip() + "\n\n", content, flags=re.DOTALL)
                else:
                    content += attachment_section

                stats["attachments_added"] += len(attachments_to_add)

            if content != original_content:
                # 写回文件
                md_file.write_text(content, encoding='utf-8')
                fix_count = len(matches_files) + len(matches_attach)
                attach_count = len(attachments_to_add)
                print(f"    ✅ {md_file.name}: 修复 {fix_count} 处路径, 添加 {attach_count} 个附件引用")

        except Exception as e:
            print(f"    ❌ 修复失败 {md_file.name}: {e}")
            stats["failed"] += 1
            stats["errors"].append(str(e))

    return stats


def fix_asset_paths_in_file(filepath: Path, assets_dir: Path = None) -> Tuple[int, str]:
    """
    修复单个 Markdown 文件中的附件路径

    根据附件类型使用不同路径：
    - _files: 替换为 ../assets/文件名
    - _Attachments: 替换为 ../assets/attachments/目录名/文件名，并在尾部添加附件区域

    Args:
        filepath: Markdown 文件路径
        assets_dir: assets 目录路径（可选，用于计算相对路径）

    Returns:
        tuple: (修复的路径数量, 错误信息或空字符串)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        fix_count = 0

        # 收集 _Attachments 引用
        attachments_to_add = []

        # 处理 _files 格式
        # 原: ![xxx](笔记名_files/abc.png)
        # 替: ![xxx](../assets/abc.png)
        pattern_files = re.compile(r'(!?)\[([^\]]*)\]\(([^\s\[]+)_files/([^)]+)\)')
        for prefix, alt_text, note_name, file_name in pattern_files.findall(content):
            old_pattern = f"{prefix}[{alt_text}]({note_name}_files/{file_name})"
            display_text = alt_text if alt_text else file_name
            new_pattern = f"{prefix}[{display_text}](../assets/{file_name})"
            content = content.replace(old_pattern, new_pattern)
            fix_count += 1

        # 处理 _Attachments 格式
        # 原: ![xxx](笔记名_Attachments/abc.png)
        # 替: 在尾部统一添加附件引用
        pattern_attach = re.compile(r'(!?)\[([^\]]*)\]\(([^\s\[]+)_Attachments/([^)]+)\)')
        for prefix, alt_text, note_name, file_name in pattern_attach.findall(content):
            old_pattern = f"{prefix}[{alt_text}]({note_name}_Attachments/{file_name})"
            attachments_to_add.append(file_name)
            content = content.replace(old_pattern, '')
            content = re.sub(r'^\s*$', '\n', content)
            fix_count += 1

        # 如果有 _Attachments，在尾部添加附件区域
        if attachments_to_add:
            note_name = filepath.stem
            attachment_section = "\n\n---\n\n## 附件\n\n"
            for file_name in attachments_to_add:
                attachment_dir = f"{note_name}_Attachments"
                attachment_path = f"../assets/attachments/{attachment_dir}/{file_name}"
                attachment_section += f"![{file_name}]({attachment_path})\n\n"

            if "\n\n## 附件\n" in content:
                content = re.sub(r'\n\n## 附件\n\n.*?(?=\n\n## |\n\n---\n\n$|$)',
                                attachment_section.strip() + "\n\n", content, flags=re.DOTALL)
            else:
                content += attachment_section

        if fix_count > 0:
            filepath.write_text(content, encoding='utf-8')

        return fix_count, ""

    except Exception as e:
        return 0, str(e)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        md_dir = sys.argv[1]
        graph_dir = sys.argv[2]
        result = run_logseq_migration(md_dir, graph_dir)
        print(result)
    else:
        print("使用方法:")
        print("  python logseq_migrator.py <Markdown目录> <Logseq图谱目录>")
        print("\n示例:")
        print('  python logseq_migrator.py "G:\\Data\\wiz\\markdown" "C:\\Users\\Admin\\Logseq\\my-graph"')