import sys
import os
# 添加脚本目录到路径
sys.path.insert(0, r'C:\Users\Administrator\.codebuddy\skills\wiz-migration\scripts')

# 导入模块测试
from detector import detect_wiz_data_dir
from guide_generator import generate_export_guide
from migrator import run_attachment_migration

# 测试 detect_wiz_data_dir
result = detect_wiz_data_dir()
print(f"detect_wiz_data_dir 结果: {result}")

# 测试生成导出指南 - 使用临时目录
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    guide_path = generate_export_guide(tmpdir)
    print(f"generate_export_guide 结果: {guide_path}")
    print(f"文件是否存在: {os.path.exists(guide_path)}")

print("\n所有测试通过!")