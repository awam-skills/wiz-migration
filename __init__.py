"""
为知笔记迁移技能 - Python 包入口

提供完整的为知笔记数据迁移功能：
1. 自动检测为知笔记数据目录
2. 生成详细导出操作指南
3. 批量迁移附件文件
"""

__version__ = "1.0.0"
__author__ = "OpenClaw Assistant"

from scripts.detector import detect_wiz_data_dir, validate_data_dir
from scripts.guide_generator import generate_export_guide, append_migration_log
from scripts.migrator import run_attachment_migration, find_attachments
from scripts.pandoc_converter import (
    check_pandoc_installed,
    get_pandoc_version,
    ensure_pandoc,
    convert_html_to_markdown,
    batch_convert,
    convert_with_pandoc,
    interactive_convert
)

__all__ = [
    # 检测功能
    "detect_wiz_data_dir",
    "validate_data_dir",
    # 导出指南
    "generate_export_guide",
    "append_migration_log",
    # 附件迁移
    "run_attachment_migration",
    "find_attachments",
    # Pandoc 转换
    "check_pandoc_installed",
    "get_pandoc_version",
    "ensure_pandoc",
    "convert_html_to_markdown",
    "batch_convert",
    "convert_with_pandoc",
    "interactive_convert",
    # 向导
    "start_wizard"
]

# 导入主程序中的 start_wizard 函数
try:
    from bin.wiz-migrate import start_wizard
    __all__.append("start_wizard")
except ImportError:
    pass


def quick_start():
    """
    快速启动向导
    
    相当于: start_wizard()
    """
    from bin.wiz-migrate import start_wizard
    start_wizard()


if __name__ == "__main__":
    quick_start()
