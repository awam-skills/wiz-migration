#!/usr/bin/env python3
"""
为知笔记导出指南生成器
将导出要求转换为 Markdown 模板
"""

from pathlib import Path
from datetime import datetime


def generate_export_guide(export_dir):
    """
    返回简化的导出操作指南文本

    Args:
        export_dir: 导出目录路径

    Returns:
        str: 简化的指南文本
    """
    return f"""导出操作步骤：

1. 在左侧笔记本列表，选中要导出的笔记本（可多选）
2. 右键 → "导出文件" → 选择 "导出 HTML"
3. 在导出对话框中选择 "多个网页文件（含附件）"
4. 选择目标文件夹：{export_dir}
5. 点击确定导出

完成后返回本向导继续。
"""


def append_migration_log(export_dir, status, notes=""):
    """
    记录导出操作日志
    
    Args:
        export_dir: 导出目录
        status: 状态（completed/failed/partial）
        notes: 备注信息
    """
    log_path = Path("migration_log.json")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "export_dir": export_dir,
        "status": status,
        "notes": notes
    }
    
    if log_path.exists():
        import json
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    return str(log_path)


if __name__ == "__main__":
    # 测试
    test_dir = input("测试导出目录路径: ").strip() or r"C:\Wiz_Export"
    output = generate_export_guide(test_dir)
    print(f"指南已生成: {output}")
