#!/usr/bin/env python3
"""
Pandoc 转换器模块 - HTML → Markdown 批量转换

功能：
1. 自动检测 Pandoc 是否已安装
2. 自动安装 Pandoc（跨平台支持）
3. 批量转换 HTML 文件为 Markdown
4. 保留附件引用（_files 目录）
"""

import os
import sys
import subprocess
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# ==================== html2text 安装 (Python 原生方案) ====================

def check_html2text_installed() -> bool:
    """
    检测 html2text 是否已安装

    Returns:
        bool: html2text 是否可用
    """
    try:
        import html2text
        return True
    except ImportError:
        return False


def get_html2text_version() -> Optional[str]:
    """
    获取 html2text 版本号

    Returns:
        str: 版本号，失败返回 None
    """
    try:
        import html2text
        return getattr(html2text, '__version__', 'unknown')
    except ImportError:
        return None


def install_html2text() -> bool:
    """
    使用 pip 安装 html2text

    Returns:
        bool: 安装是否成功
    """
    print("正在使用 pip 安装 html2text...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'html2text'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("  ✅ pip 安装 html2text 成功")
            return True
        else:
            print(f"  ⚠️  pip 安装失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  pip 安装超时")
        return False
    except Exception as e:
        print(f"  ⚠️  pip 安装失败: {e}")
        return False


def ensure_html2text(auto_install: bool = True) -> bool:
    """
    确保 html2text 可用，如未安装则尝试安装

    Args:
        auto_install: 是否自动安装，默认 True

    Returns:
        bool: html2text 是否可用
    """
    if check_html2text_installed():
        version = get_html2text_version()
        print(f"✅ html2text 已安装 (版本: {version})")
        return True

    if not auto_install:
        print("⚠️  html2text 未安装")
        return False

    return install_html2text()


# ==================== Pandoc 安装 ====================

def check_pandoc_installed() -> bool:
    """
    检测 Pandoc 是否已安装
    
    Returns:
        bool: Pandoc 是否可用
    """
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_pandoc_version() -> Optional[str]:
    """
    获取 Pandoc 版本号
    
    Returns:
        str: 版本号，如 "3.1.13"，失败返回 None
    """
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            first_line = result.stdout.strip().split('\n')[0]
            # 提取版本号，如 "pandoc 3.1.13" -> "3.1.13"
            parts = first_line.split()
            if len(parts) >= 2:
                return parts[1]
    except Exception:
        pass
    return None


MAX_RETRIES = 2
PANDOC_INSTALL_URL = "https://pandoc.org/installing.html"


def run_with_retry(cmd: list, timeout: int = 300) -> Tuple[bool, str]:
    """
    执行命令，支持重试

    Args:
        cmd: 命令列表
        timeout: 超时时间（秒）

    Returns:
        Tuple[bool, str]: (是否成功, 错误信息)
    """
    last_error = ""

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return True, ""
            last_error = result.stderr or f"返回码: {result.returncode}"
        except subprocess.TimeoutExpired:
            last_error = "命令执行超时"
        except FileNotFoundError:
            return False, "命令不可用"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES - 1:
            print(f"    第 {attempt + 1} 次尝试失败，{MAX_RETRIES - attempt - 1} 次重试机会...")

    return False, last_error


def install_pandoc_windows() -> bool:
    """
    在 Windows 上安装 Pandoc

    尝试多种安装方式（每种方式最多重试2次）：
    1. winget（推荐）
    2. chocolatey
    3. scoop
    4. 直接下载安装包

    Returns:
        bool: 安装是否成功
    """
    print("正在尝试自动安装 Pandoc...")

    # 先检查是否已安装（可能之前安装过但路径问题）
    if check_pandoc_installed():
        version = get_pandoc_version()
        print(f"✅ Pandoc 已安装 (版本: {version})")
        return True

    # 方法1: 使用 winget
    print("  尝试使用 winget 安装...")
    success, error = run_with_retry([
        'winget', 'install', '--id', 'JohnMacFarlane.Pandoc', '-e',
        '--silent', '--accept-package-agreements', '--accept-source-agreements'
    ])
    if success:
        print("  ✅ winget 安装成功")
        return True
    else:
        print(f"  ⚠️  winget 安装失败: {error}")

    # 方法2: 使用 chocolatey
    print("  尝试使用 chocolatey 安装...")
    success, error = run_with_retry([
        'choco', 'install', 'pandoc', '-y'
    ])
    if success:
        print("  ✅ chocolatey 安装成功")
        return True
    else:
        print(f"  ⚠️  chocolatey 安装失败: {error}")

    # 方法3: 使用 scoop
    print("  尝试使用 scoop 安装...")
    success, error = run_with_retry([
        'scoop', 'install', 'pandoc'
    ])
    if success or check_pandoc_installed():
        print("  ✅ scoop 安装成功")
        return True
    else:
        print(f"  ⚠️  scoop 安装失败: {error}")

    # 方法4: 手动下载（最后备选）
    print("\n" + "=" * 50)
    print("  ⚠️  自动安装失败，请手动安装 Pandoc")
    print("=" * 50)
    print(f"\n  📦 安装文档: {PANDOC_INSTALL_URL}")
    print("  💻 Windows 推荐: https://github.com/jgm/pandoc/releases/latest")
    print("\n  安装完成后，请重新运行此程序。")

    return False


def install_pandoc_macos() -> bool:
    """
    在 macOS 上安装 Pandoc
    
    尝试：
    1. Homebrew
    2. MacPorts
    
    Returns:
        bool: 安装是否成功
    """
    print("正在尝试自动安装 Pandoc (macOS)...")
    
    # 方法1: Homebrew
    print("  尝试使用 Homebrew 安装...")
    try:
        result = subprocess.run(
            ['brew', 'install', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("  ✅ Homebrew 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  Homebrew 不可用")
    except Exception as e:
        print(f"  ⚠️  Homebrew 安装失败: {e}")

    # 方法2: MacPorts
    print("  尝试使用 MacPorts 安装...")
    try:
        result = subprocess.run(
            ['sudo', 'port', 'install', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("  ✅ MacPorts 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  MacPorts 不可用")
    except Exception as e:
        print(f"  ⚠️  MacPorts 安装失败: {e}")

    print("  ⚠️  自动安装失败，请手动安装 Pandoc")
    print("  使用 Homebrew: brew install pandoc")
    print("  或下载: https://pandoc.org/installing.html")
    
    return False


def install_pandoc_linux() -> bool:
    """
    在 Linux 上安装 Pandoc
    
    尝试：
    1. apt (Debian/Ubuntu)
    2. dnf (Fedora)
    3. yum (CentOS)
    4. pacman (Arch)
    
    Returns:
        bool: 安装是否成功
    """
    print("正在尝试自动安装 Pandoc (Linux)...")
    
    # 方法1: apt
    print("  尝试使用 apt 安装...")
    try:
        # 先更新包列表
        subprocess.run(
            ['sudo', 'apt', 'update'],
            capture_output=True,
            timeout=120
        )
        result = subprocess.run(
            ['sudo', 'apt', 'install', '-y', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            print("  ✅ apt 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  apt 不可用")
    except Exception as e:
        print(f"  ⚠️  apt 安装失败: {e}")

    # 方法2: dnf
    print("  尝试使用 dnf 安装...")
    try:
        result = subprocess.run(
            ['sudo', 'dnf', 'install', '-y', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            print("  ✅ dnf 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  dnf 不可用")
    except Exception as e:
        print(f"  ⚠️  dnf 安装失败: {e}")

    # 方法3: yum
    print("  尝试使用 yum 安装...")
    try:
        result = subprocess.run(
            ['sudo', 'yum', 'install', '-y', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            print("  ✅ yum 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  yum 不可用")
    except Exception as e:
        print(f"  ⚠️  yum 安装失败: {e}")

    # 方法4: pacman
    print("  尝试使用 pacman 安装...")
    try:
        result = subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', 'pandoc'],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            print("  ✅ pacman 安装成功")
            return True
    except FileNotFoundError:
        print("  ⚠️  pacman 不可用")
    except Exception as e:
        print(f"  ⚠️  pacman 安装失败: {e}")

    print("  ⚠️  自动安装失败，请手动安装 Pandoc")
    print("  Ubuntu/Debian: sudo apt install pandoc")
    print("  Fedora: sudo dnf install pandoc")
    print("  Arch: sudo pacman -S pandoc")
    print("  或下载: https://pandoc.org/installing.html")
    
    return False


def ensure_pandoc(auto_install: bool = True) -> bool:
    """
    确保 Pandoc 可用，如未安装则尝试安装
    
    Args:
        auto_install: 是否自动安装，默认 True
        
    Returns:
        bool: Pandoc 是否可用
    """
    # 检查是否已安装
    if check_pandoc_installed():
        version = get_pandoc_version()
        print(f"✅ Pandoc 已安装 (版本: {version})")
        return True
    
    if not auto_install:
        print("⚠️  Pandoc 未安装")
        return False
    
    # 根据系统类型尝试安装
    system = sys.platform
    
    if system == 'win32':
        return install_pandoc_windows()
    elif system == 'darwin':
        return install_pandoc_macos()
    elif system.startswith('linux'):
        return install_pandoc_linux()
    else:
        print(f"⚠️  不支持的系统类型: {system}")
        print("请手动安装 Pandoc: https://pandoc.org/installing.html")
        return False


# ==================== HTML 转换 ====================

def find_html_files(directory: str) -> List[Path]:
    """
    查找目录下所有 HTML 文件
    
    Args:
        directory: 要搜索的目录
        
    Returns:
        List[Path]: HTML 文件路径列表
    """
    html_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    for html_file in dir_path.rglob('*.html'):
        # 跳过 _Attachments 目录下的 HTML 文件
        if any(part.endswith("_Attachments") for part in html_file.parts):
            continue
        html_files.append(html_file)
    
    return sorted(html_files)


def convert_html_to_markdown(
    html_path: Path,
    output_path: Optional[Path] = None,
    preserve_links: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    将单个 HTML 文件转换为 Markdown

    Args:
        html_path: HTML 文件路径
        output_path: 输出 Markdown 路径，默认与 HTML 同名但扩展名为 .md
        preserve_links: 是否保留链接为 Markdown 格式

    Returns:
        Tuple[bool, Optional[str]]: (是否成功, 错误信息)
    """
    if not html_path.exists():
        return False, f"文件不存在: {html_path}"

    # 确定输出路径
    if output_path is None:
        output_path = html_path.with_suffix('.md')

    # 构建 Pandoc 命令
    # -f html: 从 HTML 格式输入
    # -t markdown-raw_html-native_divs-fenced_divs-bracketed_spans:
    #   - raw_html: 保留原始 HTML
    #   - native_divs: 使用原生 div 标签
    #   - -fenced_divs: 禁用 ::: 容器语法
    #   - bracketed_spans: 支持括号 span 语法
    # -s: standalone（包含必要的元数据）
    # --wrap=none: 不自动换行
    # --preserve-tabs: 保留制表符
    # -L: 使用 Lua 过滤器移除 style/class 等属性
    lua_filter = Path(__file__).parent / 'remove_attrs.lua'
    cmd = [
        'pandoc',
        '-f', 'html',
        '-t', 'markdown-raw_html-native_divs-fenced_divs-bracketed_spans',
        '-s',
        '--wrap=none',
        '--preserve-tabs',
        '-L', str(lua_filter),
        str(html_path),
        '-o', str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # 后处理：修复附件引用路径
            if preserve_links:
                _fix_attachment_references(output_path, html_path.parent)
            return True, None
        else:
            error_msg = result.stderr or "未知错误"
            return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "转换超时"
    except Exception as e:
        return False, str(e)


def _fix_attachment_references(md_path: Path, html_dir: Path):
    """
    修复 Markdown 文件中的附件引用路径
    
    为知笔记导出的 HTML 中，附件引用通常是相对路径如：
    笔记1_files/image.png
    
    转换为 Markdown 后，需要确保引用正确
    
    Args:
        md_path: Markdown 文件路径
        html_dir: HTML 文件所在目录
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有 _files 目录
        html_dir_name = html_dir.name
        if html_dir_name.endswith('_files'):
            # HTML 文件在 _files 同级目录，不需要修改
            return
        
        # 查找对应的 _files 目录
        files_dir = html_dir / f"{html_dir.stem}_files"
        if not files_dir.exists():
            # 尝试其他命名模式
            for item in html_dir.iterdir():
                if item.is_dir() and item.name.endswith('_files'):
                    files_dir = item
                    break
            else:
                return
        
        # 不需要修改，因为 Pandoc 已经正确处理了相对路径
        # 这里可以添加额外的路径修复逻辑
        
        # 保存修改
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception:
        pass  # 静默处理错误


def batch_convert(
    source_dir: str,
    output_dir: Optional[str] = None,
    recursive: bool = True,
    skip_existing: bool = True,
    verbose: bool = True
) -> Dict:
    """
    批量转换 HTML 文件为 Markdown
    
    Args:
        source_dir: 源目录（包含 HTML 文件）
        output_dir: 输出目录，默认与源目录相同
        recursive: 是否递归搜索子目录
        skip_existing: 是否跳过已存在的 Markdown 文件
        verbose: 是否显示详细输出
        
    Returns:
        Dict: 转换结果统计
    """
    source_path = Path(source_dir)
    if not source_path.exists():
        return {
            'success': False,
            'error': f"目录不存在: {source_dir}",
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0
        }
    
    # 确定输出目录
    if output_dir is None:
        output_dir = source_dir
    output_path = Path(output_dir)
    
    # 查找所有 HTML 文件
    html_files = find_html_files(source_dir)
    
    if not html_files:
        return {
            'success': True,
            'message': '未找到 HTML 文件',
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0
        }
    
    if verbose:
        print(f"找到 {len(html_files)} 个 HTML 文件")
        print(f"源目录: {source_dir}")
        print(f"输出目录: {output_dir}")
        print()
    
    # 统计
    converted = 0
    skipped = 0
    failed = 0
    errors = []

    # 文件存在策略
    _file_exists_strategy = None

    for html_file in html_files:
        # 计算相对路径
        rel_path = html_file.relative_to(source_path)

        # 计算输出路径
        md_file = output_path / rel_path.with_suffix('.md')

        # 检查文件是否已存在
        if md_file.exists():
            # 首次遇到已存在文件，询问策略
            if _file_exists_strategy is None and not skip_existing:
                print("\n" + "=" * 60)
                print("⚠️  检测到目标 Markdown 文件已存在")
                print("=" * 60)
                print(f"文件: {rel_path}")
                print("\n请选择处理策略（本次转换全程有效）:")
                print("  1. 覆盖 (overwrite) - 替换已有 Markdown 文件")
                print("  2. 跳过 (skip) - 保留已有文件，不转换")
                print("  3. 覆盖所有 (overwrite-all) - 覆盖此文件及后续所有已存在文件")
                print("  4. 跳过所有 (skip-all) - 跳过此文件及后续所有已存在文件")

                while True:
                    choice = input("\n请输入选择 (1/2/3/4): ").strip()
                    if choice == '1':
                        _file_exists_strategy = 'overwrite'
                        print("✅ 已选择: 覆盖已有文件")
                        break
                    elif choice == '2':
                        _file_exists_strategy = 'skip'
                        print("⏭️  已选择: 跳过已有文件")
                        break
                    elif choice == '3':
                        _file_exists_strategy = 'overwrite-all'
                        print("✅ 已选择: 覆盖已有文件（全部）")
                        break
                    elif choice == '4':
                        _file_exists_strategy = 'skip-all'
                        print("⏭️  已选择: 跳过已有文件（全部）")
                        break
                    else:
                        print("无效选择，请输入 1、2、3 或 4")

            # 根据策略处理
            if skip_existing or _file_exists_strategy in ('skip', 'skip-all'):
                if verbose:
                    print(f"⏭️  跳过: {rel_path}")
                skipped += 1
                continue
            elif _file_exists_strategy in ('overwrite', 'overwrite-all'):
                if verbose:
                    print(f"🔄 覆盖: {rel_path}")
                # 继续执行转换（会覆盖已有文件）
            else:
                # 默认跳过
                if verbose:
                    print(f"⏭️  跳过: {rel_path}")
                skipped += 1
                continue
        
        # 确保输出目录存在
        md_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换
        if verbose:
            print(f"🔄 转换: {rel_path} -> {md_file.name}")
        
        success, error = convert_html_to_markdown(html_file, md_file)
        
        if success:
            converted += 1
            if verbose:
                print(f"  ✅ 成功")
        else:
            failed += 1
            errors.append((str(rel_path), error))
            if verbose:
                print(f"  ❌ 失败: {error}")
    
    result = {
        'success': failed == 0,
        'total': len(html_files),
        'converted': converted,
        'skipped': skipped,
        'failed': failed,
        'errors': errors
    }
    
    if verbose:
        print()
        print("=" * 50)
        print(f"转换完成:")
        print(f"  ✅ 成功: {converted}")
        print(f"  ⏭️  跳过: {skipped}")
        print(f"  ❌ 失败: {failed}")
        print("=" * 50)

        if errors:
            print("\n错误详情:")
            for file_path, error in errors[:10]:  # 最多显示10个
                print(f"  • {file_path}: {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")

            # 生成错误报告文件
            error_report_path = _generate_error_report(
                source_dir, errors, output_path
            )
            if error_report_path:
                print(f"\n📄 错误报告已生成: {error_report_path}")

    return result


def _generate_error_report(
    source_dir: str,
    errors: List[Tuple[str, str]],
    output_dir: Optional[Path] = None
) -> Optional[str]:
    """
    生成转换错误报告文件

    Args:
        source_dir: 源目录
        errors: 错误列表 [(文件路径, 错误信息), ...]
        output_dir: 输出目录

    Returns:
        str: 报告文件路径，失败返回 None
    """
    if not errors:
        return None

    try:
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"convert_error_report_{timestamp}.txt"

        if output_dir:
            report_path = Path(output_dir) / report_filename
        else:
            report_path = Path(source_dir) / report_filename

        # 写入报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("  HTML → Markdown 转换错误报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源目录: {source_dir}\n")
            f.write(f"错误数量: {len(errors)}\n\n")
            f.write("-" * 60 + "\n\n")

            for i, (file_path, error) in enumerate(errors, 1):
                f.write(f"{i}. 文件: {file_path}\n")
                f.write(f"   错误: {error}\n\n")

            f.write("-" * 60 + "\n")
            f.write("请检查以上文件的格式或内容后重试。\n")

        return str(report_path)

    except Exception as e:
        print(f"  ⚠️  生成错误报告失败: {e}")
        return None


# ==================== Python 原生转换 (html2text) ====================

def convert_html_to_markdown_with_html2text(
    html_path: Path,
    output_path: Optional[Path] = None
) -> Tuple[bool, Optional[str]]:
    """
    使用 html2text 将单个 HTML 文件转换为 Markdown（Python 原生方案）

    Args:
        html_path: HTML 文件路径
        output_path: 输出 Markdown 路径，默认与 HTML 同名但扩展名为 .md

    Returns:
        Tuple[bool, Optional[str]]: (是否成功, 错误信息)
    """
    if not html_path.exists():
        return False, f"文件不存在: {html_path}"

    try:
        import html2text
    except ImportError:
        return False, "html2text 未安装"

    # 确定输出路径
    if output_path is None:
        output_path = html_path.with_suffix('.md')

    try:
        # 读取 HTML 文件
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 创建 html2text 对象
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # 不自动换行
        h.unicode_snob = True  # 保留 Unicode 字符
        h.relative_links = True  # 保留相对链接

        # 转换
        md_content = h.handle(html_content)

        # 修复附件引用路径（保留 xxx_files/ 引用）
        md_content = _fix_html2text_attachment_references(md_content, html_path)

        # 写入 Markdown 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return True, None

    except subprocess.TimeoutExpired:
        return False, "转换超时"
    except Exception as e:
        return False, str(e)


def _fix_html2text_attachment_references(md_content: str, html_path: Path) -> str:
    """
    修复 html2text 转换后的附件引用路径

    为知笔记导出的 HTML 中，附件引用通常是相对路径如：
    笔记1_files/image.png

    html2text 可能会错误处理这些路径，需要修复

    Args:
        md_content: Markdown 内容
        html_path: HTML 文件路径

    Returns:
        str: 修复后的 Markdown 内容
    """
    import re

    html_dir = html_path.parent
    html_stem = html_path.stem  # 不带扩展名的文件名

    # 查找可能的附件引用问题
    # html2text 有时会将本地图片路径转换成绝对路径或损坏的引用

    # 修复模式1: 图片引用 - 确保 _files 目录的相对路径正确
    # 例如: ![image](../笔记1_files/image.png) -> ![image](笔记1_files/image.png)
    pattern1 = re.compile(r'!\[([^\]]*)\]\([^)]*' + re.escape(html_stem) + r'_files/([^)]+)\)')
    def fix_image_ref(m):
        # 保持相对路径格式
        return f'![{m.group(1)}]({html_stem}_files/{m.group(2)})'

    md_content = pattern1.sub(fix_image_ref, md_content)

    # 修复模式2: 确保 _files 路径引用格式正确
    # 例如: ![image](/path/to/笔记1_files/image.png) -> ![image](笔记1_files/image.png)
    pattern2 = re.compile(r'!\[([^\]]*)\]\[[^\]]*' + re.escape(html_stem) + r'_files/([^)\]]+)\]')
    def fix_image_ref2(m):
        alt_text = m.group(1)
        filename = m.group(2)
        return f'![{alt_text}]({html_stem}_files/{filename})'

    md_content = pattern2.sub(fix_image_ref2, md_content)

    return md_content


def batch_convert_with_html2text(
    source_dir: str,
    output_dir: Optional[str] = None,
    recursive: bool = True,
    skip_existing: bool = True,
    verbose: bool = True
) -> Dict:
    """
    批量转换 HTML 文件为 Markdown（使用 html2text）

    Args:
        source_dir: 源目录（包含 HTML 文件）
        output_dir: 输出目录，默认与源目录相同
        recursive: 是否递归搜索子目录
        skip_existing: 是否跳过已存在的 Markdown 文件
        verbose: 是否显示详细输出

    Returns:
        Dict: 转换结果统计
    """
    source_path = Path(source_dir)
    if not source_path.exists():
        return {
            'success': False,
            'error': f"目录不存在: {source_dir}",
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0
        }

    # 确定输出目录
    if output_dir is None:
        output_dir = source_dir
    output_path = Path(output_dir)

    # 查找所有 HTML 文件
    html_files = find_html_files(source_dir)

    if not html_files:
        return {
            'success': True,
            'message': '未找到 HTML 文件',
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0
        }

    if verbose:
        print(f"找到 {len(html_files)} 个 HTML 文件")
        print(f"源目录: {source_dir}")
        print(f"输出目录: {output_dir}")
        print()

    # 统计
    converted = 0
    skipped = 0
    failed = 0
    errors = []

    # 文件存在策略
    _file_exists_strategy = None

    for html_file in html_files:
        # 计算相对路径
        rel_path = html_file.relative_to(source_path)

        # 计算输出路径
        md_file = output_path / rel_path.with_suffix('.md')

        # 检查文件是否已存在
        if md_file.exists():
            # 首次遇到已存在文件，询问策略
            if _file_exists_strategy is None and not skip_existing:
                print("\n" + "=" * 60)
                print("⚠️  检测到目标 Markdown 文件已存在")
                print("=" * 60)
                print(f"文件: {rel_path}")
                print("\n请选择处理策略（本次转换全程有效）:")
                print("  1. 覆盖 (overwrite) - 替换已有 Markdown 文件")
                print("  2. 跳过 (skip) - 保留已有文件，不转换")
                print("  3. 覆盖所有 (overwrite-all) - 覆盖此文件及后续所有已存在文件")
                print("  4. 跳过所有 (skip-all) - 跳过此文件及后续所有已存在文件")

                while True:
                    choice = input("\n请输入选择 (1/2/3/4): ").strip()
                    if choice == '1':
                        _file_exists_strategy = 'overwrite'
                        print("✅ 已选择: 覆盖已有文件")
                        break
                    elif choice == '2':
                        _file_exists_strategy = 'skip'
                        print("⏭️  已选择: 跳过已有文件")
                        break
                    elif choice == '3':
                        _file_exists_strategy = 'overwrite-all'
                        print("✅ 已选择: 覆盖已有文件（全部）")
                        break
                    elif choice == '4':
                        _file_exists_strategy = 'skip-all'
                        print("⏭️  已选择: 跳过已有文件（全部）")
                        break
                    else:
                        print("无效选择，请输入 1、2、3 或 4")

            # 根据策略处理
            if skip_existing or _file_exists_strategy in ('skip', 'skip-all'):
                if verbose:
                    print(f"⏭️  跳过: {rel_path}")
                skipped += 1
                continue
            elif _file_exists_strategy in ('overwrite', 'overwrite-all'):
                if verbose:
                    print(f"🔄 覆盖: {rel_path}")
                # 继续执行转换（会覆盖已有文件）
            else:
                # 默认跳过
                if verbose:
                    print(f"⏭️  跳过: {rel_path}")
                skipped += 1
                continue

        # 确保输出目录存在
        md_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换
        if verbose:
            print(f"🔄 转换: {rel_path} -> {md_file.name}")

        success, error = convert_html_to_markdown_with_html2text(html_file, md_file)

        if success:
            converted += 1
            if verbose:
                print(f"  ✅ 成功")
        else:
            failed += 1
            errors.append((str(rel_path), error))
            if verbose:
                print(f"  ❌ 失败: {error}")

    result = {
        'success': failed == 0,
        'total': len(html_files),
        'converted': converted,
        'skipped': skipped,
        'failed': failed,
        'errors': errors
    }

    if verbose:
        print()
        print("=" * 50)
        print(f"转换完成:")
        print(f"  ✅ 成功: {converted}")
        print(f"  ⏭️  跳过: {skipped}")
        print(f"  ❌ 失败: {failed}")
        print("=" * 50)

        if errors:
            print("\n错误详情:")
            for file_path, error in errors[:10]:  # 最多显示10个
                print(f"  • {file_path}: {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")

            # 生成错误报告文件
            error_report_path = _generate_error_report(
                source_dir, errors, output_path
            )
            if error_report_path:
                print(f"\n📄 错误报告已生成: {error_report_path}")

    return result


def convert_with_html2text(
    export_dir: str,
    output_dir: Optional[str] = None,
    auto_install: bool = True,
    skip_existing: bool = True,
    verbose: bool = True
) -> Dict:
    """
    一键转换：确保 html2text 可用并批量转换（Python 原生方案）

    Args:
        export_dir: 为知笔记导出目录（包含 HTML 文件）
        output_dir: 输出目录，默认与源目录相同
        auto_install: 是否自动安装 html2text
        skip_existing: 是否跳过已存在的 Markdown 文件
        verbose: 是否显示详细输出

    Returns:
        Dict: 转换结果
    """
    if verbose:
        print("=" * 60)
        print("  为知笔记 HTML → Markdown 转换工具 (html2text)")
        print("=" * 60)
        print()

    # 1. 确保 html2text 可用
    if verbose:
        print("步骤1: 检查 html2text 安装状态")

    if not ensure_html2text(auto_install=auto_install):
        return {
            'success': False,
            'error': 'html2text 未安装且自动安装失败',
            'converted': 0,
            'failed': 0
        }

    if verbose:
        print()
        print("步骤2: 开始批量转换")
        print("-" * 60)

    # 2. 批量转换
    result = batch_convert_with_html2text(
        source_dir=export_dir,
        output_dir=output_dir,
        skip_existing=skip_existing,
        verbose=verbose
    )

    if verbose:
        print()
        if result['success']:
            print("🎉 转换完成！")
        else:
            print("⚠️ 转换完成，但有部分文件失败")

    return result


# ==================== 主函数 ====================

def convert_with_pandoc(
    export_dir: str,
    output_dir: Optional[str] = None,
    auto_install: bool = True,
    skip_existing: bool = True,
    verbose: bool = True
) -> Dict:
    """
    一键转换：确保 Pandoc 可用并批量转换
    
    Args:
        export_dir: 为知笔记导出目录（包含 HTML 文件）
        output_dir: 输出目录，默认与源目录相同
        auto_install: 是否自动安装 Pandoc
        skip_existing: 是否跳过已存在的 Markdown 文件
        verbose: 是否显示详细输出
        
    Returns:
        Dict: 转换结果
    """
    if verbose:
        print("=" * 60)
        print("  为知笔记 HTML → Markdown 转换工具")
        print("=" * 60)
        print()
    
    # 1. 确保 Pandoc 可用
    if verbose:
        print("步骤1: 检查 Pandoc 安装状态")
    
    if not ensure_pandoc(auto_install=auto_install):
        return {
            'success': False,
            'error': 'Pandoc 未安装且自动安装失败',
            'converted': 0,
            'failed': 0
        }
    
    if verbose:
        print()
        print("步骤2: 开始批量转换")
        print("-" * 60)
    
    # 2. 批量转换
    result = batch_convert(
        source_dir=export_dir,
        output_dir=output_dir,
        skip_existing=skip_existing,
        verbose=verbose
    )
    
    if verbose:
        print()
        if result['success']:
            print("🎉 转换完成！")
        else:
            print("⚠️ 转换完成，但有部分文件失败")
    
    return result


def interactive_convert():
    """
    交互式转换流程
    """
    import os
    
    print("=" * 60)
    print("  HTML → Markdown 批量转换向导")
    print("=" * 60)
    print()
    
    # 获取导出目录
    print("请输入为知笔记导出目录路径（包含 HTML 文件的文件夹）")
    export_dir = input("路径: ").strip()
    
    while not export_dir or not os.path.exists(export_dir):
        if export_dir and not os.path.exists(export_dir):
            print(f"❌ 路径不存在: {export_dir}")
        else:
            print("❌ 路径不能为空")
        export_dir = input("路径: ").strip()
    
    # 获取输出目录
    print("\n请输入输出目录（回车使用与源目录相同）")
    output_dir = input("路径 [回车]: ").strip()
    if not output_dir:
        output_dir = None
    
    # 确认
    print()
    print("确认信息:")
    print(f"  源目录: {export_dir}")
    print(f"  输出目录: {output_dir or export_dir}")
    
    confirm = input("\n确认开始转换? (y/n): ").strip().lower()
    if confirm not in ('y', 'yes', '是'):
        print("已取消")
        return
    
    # 开始转换
    print()
    result = convert_with_pandoc(
        export_dir=export_dir,
        output_dir=output_dir,
        auto_install=True,
        verbose=True
    )
    
    if result.get('success'):
        print("\n✅ 转换完成！")
        print(f"成功转换: {result.get('converted', 0)} 个文件")
    else:
        print("\n❌ 转换失败")
        print(result.get('error', '未知错误'))


if __name__ == "__main__":
    interactive_convert()
