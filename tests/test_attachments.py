"""
测试 _Attachments 添加功能

验证新策略是否正确工作
"""
from pathlib import Path

# 模拟的目录结构
pages_dir = Path(r"G:\Data\knowledge\wiz-c\pages")
assets_dir = Path(r"G:\Data\knowledge\wiz-c\assets")

print("测试附件添加功能")
print("=" * 60)
print(f"Pages 目录: {pages_dir}")
print(f"Assets 目录: {assets_dir}")
print()

# 1. 检查 assets/attachments 目录
attach_base_dir = assets_dir / "attachments"
if not attach_base_dir.exists():
    print(f"❌ 附件基础目录不存在: {attach_base_dir}")
else:
    print(f"✅ 附件基础目录存在: {attach_base_dir}")

    # 2. 列出所有附件目录
    attach_dirs = [d for d in attach_base_dir.iterdir() if d.is_dir()]
    print(f"\n找到 {len(attach_dirs)} 个附件目录:")

    for attach_dir in attach_dirs:
        print(f"\n  📁 {attach_dir.name}")

        # 解析对应的 Markdown 文件名
        if attach_dir.name.endswith("_Attachments"):
            md_name = attach_dir.name[:-12] + ".md"
        else:
            md_name = attach_dir.name + ".md"

        print(f"    对应的 MD 文件: {md_name}")

        # 在 pages 目录中查找
        md_file = None
        for md in pages_dir.rglob("*.md"):
            if md.name == md_name:
                md_file = md
                break

        if md_file:
            print(f"    ✅ 找到 MD: {md_file.relative_to(pages_dir)}")

            # 收集附件文件
            files = []
            for item in attach_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(attach_dir)
                    files.append(str(rel_path).replace('\\', '/'))

            print(f"    📄 附件文件: {len(files)} 个")
            for f in files[:5]:  # 只显示前5个
                print(f"      - {f}")
            if len(files) > 5:
                print(f"      ... 还有 {len(files) - 5} 个")
        else:
            print(f"    ❌ 未找到对应的 MD 文件")

print("\n" + "=" * 60)
print("测试完成")
