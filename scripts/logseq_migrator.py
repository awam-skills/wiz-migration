#!/usr/bin/env python3
"""
Logseq 迁移模块
将 Markdown 文件和附件迁移到 Logseq 图谱
"""

import os
import re
import shutil
import hashlib
import json
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
    print("  1. 覆盖 (overwrite) - 覆盖所有已存在的文件")
    print("  2. 跳过 (skip) - 跳过所有已存在的文件")
    print("  3. 重命名 (rename) - 自动重命名新文件（添加序号）")

    while True:
        choice = input("\n请输入选择 (1/2/3，直接回车默认1): ").strip()
        if choice == '' or choice == '1':
            _file_exists_strategy = 'overwrite_all'
            print("✅ 已选择: 覆盖所有已存在的文件")
            break
        elif choice == '2':
            _file_exists_strategy = 'skip_all'
            print("⏭️  已选择: 跳过所有已存在的文件")
            break
        elif choice == '3':
            _file_exists_strategy = 'rename'
            print("📝 已选择: 自动重命名")
            break
        else:
            print("无效选择，请输入 1、2、3、4 或 5")

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
        return {"success": False, "error": f"转化后导出目录不存在: {graph}"}

    results = {
        "success": True,
        "attachments_copied": 0,
        "attachments_skipped": 0,
        "attachments_failed": 0,
        "attachments_added": 0,
        "attach_dirs_processed": 0,
        "attach_dirs_not_found": 0,
        "attach_dirs_failed": 0,
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
    print(f"📁 Logseq 转化后导出目录: {graph}")
    print(f"📁 Pages 目录: {pages_dir}")
    print(f"📁 Assets 目录: {assets_dir}")

    # 加载附件映射（如果存在）
    attachment_mapping = {}
    mapping_file = md_dir / ".attachment_mapping.json"
    if mapping_file.exists():
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                attachment_mapping = json.load(f)
            print(f"\n📋 已加载附件映射: {len(attachment_mapping)} 个笔记")
        except Exception as e:
            print(f"\n⚠️  附件映射加载失败: {e}")
    else:
        print("\n⚠️  未找到附件映射文件，将使用默认匹配规则")

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

    # 步骤3: 添加 _Attachments 引用到 Markdown
    print("\n" + "=" * 60)
    print("步骤 3: 添加附件区域")
    print("=" * 60)

    # 从 assets/attachments 扫描并添加到 Markdown
    # 注意：使用 target_pages_dir，因为 Markdown 可能被放在了子目录下
    attach_add_stats = _add_attachments_from_assets(target_pages_dir, assets_dir)
    results["attachments_added"] = attach_add_stats["added"]
    results["attach_dirs_processed"] = attach_add_stats["processed"]
    results["attach_dirs_not_found"] = attach_add_stats["not_found"]
    results["attach_dirs_failed"] = attach_add_stats["failed"]

    # 步骤4: 批量替换附件路径（_files）
    print("\n" + "=" * 60)
    print("步骤 4: 修复 _files 路径")
    print("=" * 60)

    # 修复 pages 目录下的所有 md 文件
    path_result = fix_asset_paths(pages_dir, attachment_mapping)
    results["paths_fixed"] = path_result["fixed"]
    results["paths_failed"] = path_result["failed"]

    # 如果有子目录，也需要处理
    if move_to_subdir and (pages_dir / move_to_subdir).exists():
        path_result2 = fix_asset_paths(pages_dir / move_to_subdir, attachment_mapping)
        results["paths_fixed"] += path_result2["fixed"]
        results["paths_failed"] += path_result2["failed"]




    # 输出总结
    print("\n" + "=" * 60)
    print("迁移完成!")
    print("=" * 60)
    print(f"  ✅ 附件已复制到 assets/: {results['attachments_copied']} 个")
    if results.get('attachments_skipped', 0) > 0:
        print(f"  ⏭️  附件已存在跳过: {results['attachments_skipped']} 个")
    if results.get('attachments_failed', 0) > 0:
        print(f"  ❌ 附件复制失败: {results['attachments_failed']} 个")

    if results.get('attachments_added', 0) > 0:
        print(f"\n  📎 附件区域添加:")
        print(f"    📂 处理的附件目录: {results.get('attach_dirs_processed', 0)} 个")
        print(f"    ✅ 已添加附件引用: {results['attachments_added']} 个")
        if results.get('attach_dirs_not_found', 0) > 0:
            print(f"    ⚠️  未找到对应 Markdown: {results['attach_dirs_not_found']} 个")
        if results.get('attach_dirs_failed', 0) > 0:
            print(f"    ❌ 失败: {results['attach_dirs_failed']} 个")

    print(f"\n  ✅ Markdown 文件已复制: {results['md_files_copied']} 个")
    if results.get('md_files_skipped', 0) > 0:
        print(f"  ⏭️  Markdown 文件已存在跳过: {results['md_files_skipped']} 个")
    if results['md_files_failed'] > 0:
        print(f"  ❌ Markdown 移动失败: {results['md_files_failed']} 个")
    print(f"  ✅ 路径已修复 (_files): {results['paths_fixed']} 处")
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
    global _file_exists_strategy
    _file_exists_strategy = None  # 重置策略，每次调用都重新询问

    stats = {"copied": 0, "failed": 0, "skipped": 0, "errors": []}

    # 确保 pages 目录存在
    pages_dir.mkdir(parents=True, exist_ok=True)

    # 递归查找所有 .md 文件，保持原目录结构
    md_files = []
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        for f in files:
            if f.endswith(".md"):
                md_file = root_path / f
                # 跳过 _Attachments 目录下的 Markdown 文件
                if any(part.endswith("_Attachments") for part in md_file.parts):
                    continue
                # 跳过 _files 目录下的 Markdown 文件
                if any(part.endswith("_files") for part in md_file.parts):
                    continue
                md_files.append(md_file)

    print(f"找到 {len(md_files)} 个 Markdown 文件")

    if not md_files:
        print("⚠️  未找到 Markdown 文件")
        return stats

    # 统计同名文件（按文件名，不含路径）用于重名处理
    name_counts: Dict[str, int] = {}
    for md_file in md_files:
        file_name = md_file.name
        name_counts[file_name] = name_counts.get(file_name, 0) + 1

    # 用于检测同名已存在的文件（用于MD5比对）
    for md_file in md_files:
        try:
            # 计算相对于 source_dir 的路径，保持原目录结构
            rel_path = md_file.relative_to(source_dir)
            file_name = md_file.name

            # 对全量子目录中的重名文件，使用“相对路径前缀+文件名”扁平化到 pages 根目录
            # 示例: 01计算机/02学习方法/总结.md -> 01计算机_02学习方法_总结.md
            if name_counts.get(file_name, 0) > 1:
                rel_parts = list(rel_path.parts)
                flattened_name = "_".join(rel_parts)
                dest_file = pages_dir / flattened_name
            else:
                dest_file = pages_dir / rel_path  # 非重名文件保留原目录结构

            # 读取原始内容，并在顶部写入 Logseq 页面属性
            source_content = md_file.read_text(encoding='utf-8')
            rel_path_for_property = str(rel_path).replace("\\", "/")
            page_properties = (
                f"original-path:: {rel_path_for_property}\n"
                f"source:: 为知笔记\n\n"
            )
            new_content = page_properties + source_content

            # 确保目标目录存在
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # 处理同名文件
            if dest_file.exists():
                # 先检查 MD5 是否一致
                try:
                    src_md5 = hashlib.md5(new_content.encode('utf-8')).hexdigest()
                    dest_md5 = hashlib.md5(dest_file.read_bytes()).hexdigest()
                    if src_md5 == dest_md5:
                        print(f"    ⏭️  内容一致，跳过: {rel_path} (MD5: {src_md5[:8]}...)")
                        stats["skipped"] += 1
                        continue
                except Exception:
                    pass  # MD5 检查失败，继续使用策略处理

                strategy = ask_file_exists_strategy()


                if strategy in ['skip', 'skip_all']:
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
                elif strategy in ['overwrite', 'overwrite_all']:
                    print(f"    ⚠️  覆盖: {rel_path}")


            # 写入转换后的内容（保留原文件不变）
            dest_file.write_text(new_content, encoding='utf-8')
            stats["copied"] += 1
            if name_counts.get(file_name, 0) > 1:
                print(f"    ✅ 复制(重名重写): {rel_path} -> pages/{dest_file.name}")
            else:
                print(f"    ✅ 复制: {rel_path} -> pages/")

        except Exception as e:
            print(f"    ❌ 复制失败 {md_file.name}: {e}")
            stats["failed"] += 1
            stats["errors"].append(str(e))

    return stats


def fix_asset_paths(pages_dir: Path, attachment_mapping: Dict = None) -> Dict:
    """
    批量修复 Markdown 文件中的附件路径

    根据附件类型使用不同路径：
    - _files: 原在 Markdown 中存在，替换为 ../assets/文件名
    - _Attachments: 原不在 Markdown 中，替换为 ../assets/attachments/目录名/文件名
             并在 Markdown 尾部添加附件区域引用

    Args:
        pages_dir: Logseq pages/ 目录
        attachment_mapping: 附件映射字典（可选），包含笔记名与附件路径的对应关系

    Returns:
        dict: 统计信息
    """
    if attachment_mapping is None:
        attachment_mapping = {}

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
            # 仅匹配原始格式：笔记名_Attachments/文件
            # 不匹配已修复后的路径：../assets/attachments/笔记名_Attachments/文件
            pattern_attach = re.compile(r'(!?)\[([^\]]*)\]\(([^/\s\[]+)_Attachments/([^)]+)\)')
            matches_attach = pattern_attach.findall(content)
            if matches_attach:
                # 使用正则替换一次性移除所有 _Attachments 引用
                content = pattern_attach.sub('', content)

                # 清理多余的空行
                content = re.sub(r'\n\n+', '\n\n', content)
                content = content.strip()

                stats["fixed"] += len(matches_attach)

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


def _parse_attach_dir_to_md_name(attach_dir_name: str) -> str:
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


def _find_md_file_for_attach_dir(attach_dir_name: str, pages_dir: Path) -> Path:
    """
    在 pages 目录中查找与附件目录名匹配的 Markdown 文件

    Args:
        attach_dir_name: 附件目录名
        pages_dir: pages 目录路径

    Returns:
        匹配的 Markdown 文件路径，如果找不到返回 None
    """
    md_name = _parse_attach_dir_to_md_name(attach_dir_name)

    # 递归搜索所有 md 文件
    for md_file in pages_dir.rglob("*.md"):
        if md_file.name == md_name:
            return md_file

    return None


def _collect_attachments_from_dir(attach_dir: Path) -> List[str]:
    """
    收集附件目录中的所有文件

    Args:
        attach_dir: 附件目录路径

    Returns:
        文件名列表（使用 / 作为路径分隔符）
    """
    files = []
    print(f"    [_collect] 扫描目录: {attach_dir}")
    for item in attach_dir.rglob("*"):
        if item.is_file():
            # 保存相对路径（相对于附件目录），使用 / 作为分隔符
            rel_path = item.relative_to(attach_dir)
            file_str = str(rel_path).replace('\\', '/')
            files.append(file_str)
            print(f"    [_collect] 找到文件: {file_str}")
    print(f"    [_collect] 共找到 {len(files)} 个文件")
    return sorted(files)


def _add_attachment_section_to_md(md_file: Path, attach_files: List[str], assets_dir_name: str, pages_dir: Path = None) -> bool:
    """
    在 Markdown 文件中添加附件区域

    Args:
        md_file: Markdown 文件路径
        attach_files: 附件文件列表
        assets_dir_name: assets 目录下附件目录的名称
        pages_dir: pages 目录路径（用于计算相对路径）

    Returns:
        是否成功添加（如果文件已存在附件区域则跳过）
    """
    content = md_file.read_text(encoding='utf-8')

    # 计算相对路径
    if pages_dir is None:
        # 回退到旧的错误逻辑（为了向后兼容）
        rel_path = md_file.relative_to(md_file.parents[-1])
    else:
        rel_path = md_file.relative_to(pages_dir)
    depth = len(rel_path.parts) - 1  # 减1是因为 rel_path 包含文件名

    # 生成正确数量的 "../" 前缀
    if depth > 0:
        assets_prefix = "../" * (depth + 1)  # +1 是因为要跳出 pages/ 目录
    else:
        assets_prefix = "../"

    # 构建附件区域
    print(f"    [_add_section] attach_files = {attach_files}")
    print(f"    [_add_section] assets_dir_name = {assets_dir_name}")
    print(f"    [_add_section] depth = {depth}, assets_prefix = {assets_prefix}")

    # 如果没有附件文件，直接返回
    if not attach_files:
        print(f"    [_add_section] ⚠️ 没有附件文件，跳过添加附件区域")
        return False

    attachment_section = "\n\n---\n\n## 附件\n\n"
    for file_name in attach_files:
        attachment_path = f"{assets_prefix}assets/attachments/{assets_dir_name}/{file_name}"
        attachment_section += f"[{file_name}]({attachment_path})\n\n"
    print(f"    [_add_section] 生成的附件区域:\n{attachment_section}")


    # 检查是否已有附件区域 - 简化逻辑
    # 直接查找 ## 附件 的位置，然后移除从该位置开始的所有内容
    if "## 附件" in content:
        # 找到最后一个 ## 附件 的位置
        last_attach_pos = content.rfind("## 附件")
        # 移除从 ## 附件 开始的所有内容（包括前面的 --- 如果有的话）
        # 往前最多搜索20个字符，找 --- 或 \n\n
        search_start = max(0, last_attach_pos - 20)
        section_start = content.rfind("---\n\n", search_start, last_attach_pos)
        if section_start == -1:
            section_start = content.rfind("\n\n", search_start, last_attach_pos)
        if section_start != -1:
            content = content[:section_start]
        else:
            # 找不到分隔符，直接移除 ## 附件 及其后的内容
            content = content[:last_attach_pos]

    # 清理行尾空白并确保结尾有正确的换行
    content = content.rstrip() + "\n"
    # 添加新的附件区域
    content += attachment_section
    md_file.write_text(content, encoding='utf-8')
    return True



def _add_attachments_from_assets(
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
        md_name = _parse_attach_dir_to_md_name(attach_dir.name)
        print(f"  对应的 Markdown 文件: {md_name}")

        # 在 pages 目录中查找匹配的文件
        md_file = _find_md_file_for_attach_dir(attach_dir.name, pages_dir)

        if md_file is None:
            print(f"  ⚠️  未找到对应的 Markdown 文件")
            print(f"  [DEBUG] pages_dir = {pages_dir}")
            print(f"  [DEBUG] 将在 pages 目录中列出前10个 md 文件:")
            for i, f in enumerate(list(pages_dir.rglob("*.md"))[:10]):
                print(f"    [{i}] {f.name}")
            stats["not_found"] += 1
            continue

        print(f"  ✅ 找到 Markdown 文件: {md_file.relative_to(pages_dir)}")

        # 收集附件文件
        attach_files = _collect_attachments_from_dir(attach_dir)
        print(f"  📁 找到 {len(attach_files)} 个附件文件")

        if not attach_files:
            print(f"  ⏭️  目录为空，跳过")
            stats["skipped"] += 1
            continue

        # 添加附件区域
        try:
            result = _add_attachment_section_to_md(md_file, attach_files, attach_dir.name, pages_dir)
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
        # 仅匹配原始格式：笔记名_Attachments/文件
        # 不匹配已修复后的路径：../assets/attachments/笔记名_Attachments/文件
        pattern_attach = re.compile(r'(!?)\[([^\]]*)\]\(([^/\s\[]+)_Attachments/([^)]+)\)')
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
                attachment_section += f"[{file_name}]({attachment_path})\n\n"

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
        print("  python logseq_migrator.py <Markdown目录> <Logseq转化后导出目录>")
        print("\n示例:")
        print('  python logseq_migrator.py "G:\\Data\\wiz\\markdown" "C:\\Users\\Admin\\Logseq\\my-graph"')