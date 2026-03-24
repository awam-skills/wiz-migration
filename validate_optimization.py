#!/usr/bin/env python3
"""
验证为知笔记迁移技能优化结果
检查技能结构、文档完整性和功能可用性
"""

import os
import sys
from pathlib import Path

def check_skill_structure():
    """检查技能目录结构"""
    print("🔍 检查技能目录结构...")
    
    base_dir = Path(__file__).parent
    required_dirs = ['scripts', 'references', 'templates']
    required_files = ['SKILL.md', '__init__.py']
    
    issues = []
    
    # 检查必要目录
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            issues.append(f"❌ 缺少目录: {dir_name}")
        elif not list(dir_path.iterdir()):
            issues.append(f"⚠️  空目录: {dir_name}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    # 检查必要文件
    for file_name in required_files:
        file_path = base_dir / file_name
        if not file_path.exists():
            issues.append(f"❌ 缺少文件: {file_name}")
        else:
            print(f"✅ 文件存在: {file_name}")
    
    # 检查scripts目录内容
    scripts_dir = base_dir / 'scripts'
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.bat"))
        if script_files:
            print(f"✅ 发现 {len(script_files)} 个脚本文件")
        else:
            issues.append("❌ scripts目录中没有脚本文件")
    
    return issues

def check_skill_md():
    """检查SKILL.md质量"""
    print("\n📄 检查SKILL.md文档质量...")
    
    skill_md_path = Path(__file__).parent / 'SKILL.md'
    if not skill_md_path.exists():
        return ["❌ SKILL.md文件不存在"]
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    checks = [
        ("YAML Frontmatter", "---\nname:", "缺少YAML Frontmatter"),
        ("技能描述", "description:", "缺少description字段"),
        ("技能使用条件", "技能使用条件", "缺少'技能使用条件'部分"),
        ("核心功能概述", "核心功能概述", "缺少'核心功能概述'部分"),
        ("资源文件说明", "资源文件说明", "缺少'资源文件说明'部分"),
        ("迁移工作流", "迁移工作流执行步骤", "缺少'迁移工作流执行步骤'部分"),
    ]
    
    for check_name, pattern, error_msg in checks:
        if pattern in content:
            print(f"✅ 包含: {check_name}")
        else:
            issues.append(f"❌ {error_msg}")
    
    # 检查文档长度（简化后应该更短）
    line_count = len(content.split('\n'))
    if line_count > 500:
        issues.append(f"⚠️  文档可能过长: {line_count}行（建议≤500行）")
    else:
        print(f"✅ 文档长度合适: {line_count}行")
    
    return issues

def check_references():
    """检查参考文档"""
    print("\n📚 检查参考文档...")
    
    ref_dir = Path(__file__).parent / 'references'
    if not ref_dir.exists():
        return ["❌ references目录不存在"]
    
    ref_files = list(ref_dir.glob("*.md"))
    issues = []
    
    if ref_files:
        print(f"✅ 发现 {len(ref_files)} 个参考文档:")
        for ref_file in ref_files:
            size_kb = ref_file.stat().st_size / 1024
            print(f"   • {ref_file.name} ({size_kb:.1f} KB)")
    else:
        issues.append("❌ references目录中没有参考文档")
    
    # 检查主要参考文档
    expected_refs = [
        'wiz_directory_structure.md',
        'export_requirements.md', 
        'pandoc_usage.md'
    ]
    
    for expected in expected_refs:
        if (ref_dir / expected).exists():
            print(f"✅ 参考文档存在: {expected}")
        else:
            issues.append(f"⚠️  缺少参考文档: {expected}")
    
    return issues

def check_scripts():
    """检查脚本功能"""
    print("\n🛠️  检查脚本功能...")
    
    scripts_dir = Path(__file__).parent / 'scripts'
    if not scripts_dir.exists():
        return ["❌ scripts目录不存在"]
    
    issues = []
    required_scripts = [
        'detector.py',
        'guide_generator.py',
        'migrator.py',
        'pandoc_converter.py',
        'add_attachments.py'
    ]
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            # 检查文件是否可读
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                if first_line.startswith('#!/usr/bin/env python3'):
                    print(f"✅ 脚本格式正确: {script}")
                else:
                    print(f"✅ 脚本存在: {script}")
            except:
                issues.append(f"⚠️  脚本读取失败: {script}")
        else:
            issues.append(f"❌ 缺少脚本: {script}")
    
    # 检查总脚本数量
    all_scripts = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.bat"))
    print(f"📊 总脚本数: {len(all_scripts)}")
    
    return issues

def check_imperative_style():
    """检查是否使用imperative/infinitive form"""
    print("\n📝 检查文档编写风格...")
    
    skill_md_path = Path(__file__).parent / 'SKILL.md'
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 查找可能的问题模式
    problematic_patterns = [
        "你应该", "你需要", "你必须",  # 第二人称
        "如果", "当", "一旦",         # 条件语句开头
        "这个技能可以", "这个技能会", # 描述性而非指令性
    ]
    
    lines = content.split('\n')
    for i, line in enumerate(lines[:100], 1):  # 只检查前100行
        for pattern in problematic_patterns:
            if pattern in line:
                issues.append(f"⚠️  第{i}行可能有风格问题: {line[:60]}...")
                break
    
    if not issues:
        print("✅ 文档风格符合imperative/infinitive form")
    else:
        print("⚠️  发现可能的风格问题:")
        for issue in issues[:5]:  # 只显示前5个
            print(f"   {issue}")
        if len(issues) > 5:
            print(f"   ... 还有 {len(issues)-5} 个问题")
    
    return issues

def main():
    """主验证函数"""
    print("=" * 60)
    print("为知笔记迁移技能优化验证")
    print("=" * 60)
    
    all_issues = []
    
    # 执行各项检查
    checks = [
        ("目录结构", check_skill_structure),
        ("SKILL.md文档", check_skill_md),
        ("参考文档", check_references),
        ("脚本功能", check_scripts),
        ("文档风格", check_imperative_style),
    ]
    
    for check_name, check_func in checks:
        issues = check_func()
        all_issues.extend(issues)
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    if all_issues:
        print(f"⚠️  发现 {len(all_issues)} 个问题:")
        for issue in all_issues:
            print(f"   {issue}")
        
        error_count = sum(1 for issue in all_issues if issue.startswith('❌'))
        warning_count = sum(1 for issue in all_issues if issue.startswith('⚠️'))
        
        print(f"\n📊 统计: {error_count}个错误, {warning_count}个警告")
        
        if error_count > 0:
            print("\n❌ 验证失败: 存在必须修复的错误")
            return 1
        else:
            print("\n⚠️  验证通过但有警告: 建议修复警告项")
            return 0
    else:
        print("✅ 所有检查通过!")
        print("\n✨ 技能优化验证成功完成!")
        return 0

if __name__ == "__main__":
    sys.exit(main())