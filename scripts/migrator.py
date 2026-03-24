#!/usr/bin/env python3
"""
为知笔记附件迁移模块
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Optional, Set

# 文件存在策略: None=未选择, 'overwrite'=覆盖, 'skip'=跳过
_file_exists_strategy: Optional[str] = None


def calculate_md5(file_path: Path) -> str:
    """计算文件的 MD5 值"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def check_directory_consistency(source: Path, target: Path) -> bool:
    """
    检查源目录和目标目录的1级子目录一致性

    Args:
        source: 源目录（通常是 Data\\xxx\\all）
        target: 目标目录

    Returns:
        bool: True 表示目录一致或用户确认继续，False 表示用户取消
    """
    # 获取源目录的1级子目录
    source_dirs: Set[str] = set()
    if source.exists():
        for item in source.iterdir():
            if item.is_dir():
                source_dirs.add(item.name)

    # 获取目标目录的1级子目录
    target_dirs: Set[str] = set()
    if target.exists():
        for item in target.iterdir():
            if item.is_dir():
                target_dirs.add(item.name)

    # 计算差异
    only_in_source = source_dirs - target_dirs
    only_in_target = target_dirs - source_dirs

    if not only_in_source and not only_in_target:
        print("✅ 源目录与目标目录结构一致")
        return True

    # 存在差异，打印详细信息
    print("\n" + "=" * 60)
    print("⚠️  检测到目标路径与原始路径内文件不一致")
    print("=" * 60)

    if only_in_source:
        print(f"\n仅在源目录存在的目录 ({len(only_in_source)} 个):")
        for d in sorted(only_in_source):
            print(f"  - {d}")

    if only_in_target:
        print(f"\n仅在目标目录存在的目录 ({len(only_in_target)} 个):")
        for d in sorted(only_in_target):
            print(f"  - {d}")

    print(f"\n是否继续复制附件？")
    print("  Y - 继续（将处理所有找到的附件目录）")
    print("  N - 取消（停止本次操作）")

    while True:
        choice = input("\n请输入选择 (Y/N): ").strip().upper()
        if choice == 'Y':
            print("✅ 用户确认，继续执行")
            return True
        elif choice == 'N':
            print("❌ 用户取消操作")
            return False
        else:
            print("无效选择，请输入 Y 或 N")


def ask_file_exists_strategy() -> str:
    """询问用户文件存在时的处理策略（仅第一次询问）"""
    global _file_exists_strategy

    if _file_exists_strategy is not None:
        return _file_exists_strategy

    print("\n" + "=" * 60)
    print("⚠️  检测到目标附件目录已存在")
    print("=" * 60)
    print("请选择处理策略（本次迁移全程有效）:")
    print("  1. 覆盖 (overwrite) - 替换已有目录")
    print("  2. 跳过 (skip) - 保留已有目录，不处理")
    print("  3. 重命名 (rename) - 自动重命名新目录（添加序号）")

    while True:
        choice = input("\n请输入选择 (1/2/3): ").strip()
        if choice == '1':
            _file_exists_strategy = 'overwrite'
            print("✅ 已选择: 覆盖已有目录")
            break
        elif choice == '2':
            _file_exists_strategy = 'skip'
            print("⏭️  已选择: 跳过已有目录")
            break
        elif choice == '3':
            _file_exists_strategy = 'rename'
            print("📝 已选择: 自动重命名")
            break
        else:
            print("无效选择，请输入 1、2 或 3")

    return _file_exists_strategy


def run_attachment_migration(source_dir, target_dir, script_path=None):
    """
    运行附件迁移
    
    Args:
        source_dir: 源数据目录（包含 _Attachments）
        target_dir: 目标目录
        script_path: 可选的批处理脚本路径
        
    Returns:
        dict: 迁移结果统计
    """
    source = Path(source_dir).resolve()
    target = Path(target_dir).resolve()
    
    if not source.exists():
        raise FileNotFoundError(f"源目录不存在: {source}")
    
    # 创建目标根目录
    target.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "copied": 0,
        "skipped": 0,
        "failed": 0,
        "total_size": 0
    }
    
    print(f"正在扫描附件目录...")
    
    # 方法1: 使用批处理脚本（Windows）
    if script_path and os.name == 'nt' and Path(script_path).exists():
        return _run_batch_script(script_path, source_dir, target_dir)
    
    # 方法2: Python 实现跨平台版本
    return _copy_attachments_python(source, target, stats)


def _run_batch_script(script_path, source_dir, target_dir):
    """
    运行 Windows 批处理脚本
    
    注意：这会启动一个新进程，不是在 Python 中复制
    """
    import subprocess
    
    # 修改脚本中的路径
    script_content = Path(script_path).read_text(encoding='utf-8')
    
    # 替换路径
    script_content = script_content.replace(
        'set "SOURCE_DIR=C:\\Users\\Administrator\\Documents\\My Knowledge"',
        f'set "SOURCE_DIR={source_dir}"'
    )
    script_content = script_content.replace(
        'set "TARGET_DIR=G:\\Data\\knowledge\\wiz"',
        f'set "TARGET_DIR={target_dir}"'
    )
    
    # 写入临时脚本
    temp_script = Path("temp_copy_attachments.bat")
    temp_script.write_text(script_content, encoding='utf-8')
    
    try:
        print("正在运行批处理脚本...")
        result = subprocess.run(
            [str(temp_script)],
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"错误输出: {result.stderr}")
        
        # 解析结果（批处理脚本里的统计比较困难，简单返回）
        return {
            "copied": 0,  # 无法精确获取
            "skipped": 0,
            "failed": 0,
            "via_batch": True
        }
    finally:
        if temp_script.exists():
            temp_script.unlink()


def _copy_attachments_python(source: Path, target: Path, stats: Dict):
    """
    Python 实现附件复制

    查找并复制所有 _Attachments 目录，保持目录结构一致
    目标路径不存在时先建立，支持深度拷贝，已存在自动跳过
    """
    print(f"源目录: {source}")
    print(f"目标目录: {target}")
    print()

    # 检查是否为 all 目录（为知笔记的笔记目录）
    # all 目录下的结构是笔记本分类，不需要进行一致性检查
    is_all_dir = source.name == "all" or (source.parent.name == "all")

    if not is_all_dir:
        # 检查目录一致性（仅在非 all 目录时检查）
        if not check_directory_consistency(source, target):
            stats["cancelled"] = True
            return stats
    else:
        print("✅ 检测到为知笔记 all 目录，跳过结构一致性检查")

    # 查找所有 _Attachments 目录
    attachments_dirs = []

    # 递归查找
    for root, dirs, files in os.walk(source):
        for d in dirs:
            # 只处理文件夹，匹配 _Attachments 结尾（包括 xxx.md_Attachments）
            if d.endswith("_Attachments"):
                attachments_dirs.append(Path(root) / d)

    if not attachments_dirs:
        print("⚠️  未找到 _Attachments 或 _files 目录")
        print("请确认:")
        print("  1. 源目录是否正确")
        print("  2. 是否为导出的 Wiz 数据")
        return stats

    print(f"找到 {len(attachments_dirs)} 个附件目录\n")

    total = len(attachments_dirs)
    dir_count = 0
    skip_count = 0

    for idx, attach_dir in enumerate(attachments_dirs, 1):
        try:
            # 计算相对路径
            rel_path = attach_dir.relative_to(source)
            dest_path = target / rel_path

            print(f"[{idx}/{total}] 源目录: {attach_dir}")
            print(f"    目标路径: {dest_path}")

            if dest_path.exists():
                strategy = ask_file_exists_strategy()
                if strategy == 'skip':
                    print(f"    ⏭️  已存在，跳过")
                    skip_count += 1
                    print()
                    continue
                elif strategy == 'rename':
                    # 重命名目标目录
                    base = dest_path.stem
                    counter = 1
                    while dest_path.exists():
                        dest_path = dest_path.parent / f"{base}_{counter}"
                        counter += 1
                    print(f"    ⚠️  重命名为: {dest_path.name}")
                elif strategy == 'overwrite':
                    print(f"    ⚠️  覆盖已有目录")

            # 确保目标父目录存在
            dest_path.mkdir(parents=True, exist_ok=True)

            # 深度拷贝：复制所有文件和子目录
            file_count = 0
            for item in attach_dir.rglob("*"):
                if item.is_file():
                    rel_item_path = item.relative_to(attach_dir)
                    dest_file = dest_path / rel_item_path
                    # 确保子目录存在
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    # 复制文件
                    shutil.copy2(item, dest_file)
                    file_count += 1

            dir_count += 1
            stats["copied"] += file_count
            print(f"    ✅ 复制成功 ({file_count} 个文件)")
            print()

        except Exception as e:
            print(f"    ❌ 复制失败: {e}")
            stats["failed"] += 1
            print()

    stats["skipped"] = skip_count

    print("=" * 60)
    print("任务完成")
    print(f"  ✅ 本次新增复制: {dir_count} 个目录")
    print(f"  ⏭️  已存在跳过: {skip_count} 个目录")
    print(f"  ❌ 失败: {stats['failed']} 个")
    print("=" * 60)

    return stats


def find_attachments(source_dir):
    """
    查找所有附件目录（供外部调用）
    
    Returns:
        list: 附件目录路径列表
    """
    source = Path(source_dir)
    attachments = []
    
    for root, dirs, files in os.walk(source):
        for d in dirs:
            # 只处理文件夹，匹配 _Attachments 结尾（包括 xxx.md_Attachments）
            if d.endswith("_Attachments"):
                attachments.append(Path(root) / d)
    
    return attachments


def copy_attachments_batch(source_dir, target_dir):
    """
    批量复制附件（简化接口）
    
    Returns:
        dict: 统计信息
    """
    stats = {"copied": 0, "skipped": 0, "failed": 0}
    return run_attachment_migration(source_dir, target_dir, stats)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        source = sys.argv[1]
        target = sys.argv[2]
        result = run_attachment_migration(source, target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("使用方法:")
        print("  python migrator.py <源目录> <目标目录>")
        print("\n示例:")
        print('  python migrator.py "C:\\Users\\Admin\\Documents\\My Knowledge" "G:\\Data\\wiz"')
