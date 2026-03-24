# Pandoc 转换配置和最佳实践

## Pandoc 安装和配置

### 自动安装检测

技能包含自动安装检测逻辑：

```python
def check_pandoc_installation():
    """检查Pandoc安装状态"""
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return {'installed': True, 'version': version}
    except FileNotFoundError:
        return {'installed': False, 'version': None}
    return {'installed': False, 'version': None}
```

### 手动安装指南

如果自动安装失败，手动安装步骤：

#### Windows
1. 访问 https://pandoc.org/installing.html
2. 下载Windows安装包
3. 运行安装程序，确保勾选"Add to PATH"
4. 验证安装：`pandoc --version`

#### macOS
```bash
# 使用Homebrew
brew install pandoc

# 或使用MacPorts
sudo port install pandoc
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install pandoc

# Fedora
sudo dnf install pandoc

# Arch Linux
sudo pacman -S pandoc
```

## 转换配置选项

### 基础转换命令

HTML到Markdown的基础转换：

```bash
pandoc input.html -f html -t markdown -o output.md
```

### 技能使用的转换参数

在 `scripts/pandoc_converter.py` 中使用的配置：

```python
DEFAULT_PANDOC_ARGS = [
    '--from=html',
    '--to=markdown',
    '--wrap=none',              # 不自动换行
    '--atx-headers',           # 使用ATX风格标题
    '--reference-links',       # 使用引用式链接
    '--standalone',            # 生成完整文档
    '--extract-media=.',       # 提取媒体文件到当前目录
    '--preserve-tabs',         # 保留制表符
    '--shift-heading-level-by=0',  # 标题级别调整
]
```

### 高级转换选项

#### 编码处理
```bash
pandoc --from=html --to=markdown --encoding=utf-8
```

#### 特殊格式保留
```bash
pandoc --from=html --to=markdown \
  --preserve-tabs \
  --wrap=none \
  --no-wrap
```

#### 数学公式处理
```bash
pandoc --from=html --to=markdown \
  --mathjax \
  --webtex
```

## 为知笔记特定转换配置

### HTML清理过滤器

为知笔记导出的HTML包含特定格式，需要清理：

```lua
-- remove_attrs.lua 过滤器
function Div(el)
  -- 移除为知笔记特定的div属性
  if el.attributes['wiz-type'] then
    el.attributes['wiz-type'] = nil
  end
  return el
end

function Span(el)
  -- 清理为知笔记的span样式
  if el.attributes['style'] and string.find(el.attributes['style'], 'wiz') then
    el.attributes['style'] = nil
  end
  return el
end
```

使用过滤器：
```bash
pandoc input.html -f html -t markdown --lua-filter=remove_attrs.lua -o output.md
```

### 标题处理

为知笔记的标题可能嵌套在特定元素中：

```python
def fix_wiz_headings(html_content):
    """修复为知笔记的特殊标题格式"""
    # 将 <h1 class="wiz-title"> 转换为标准 <h1>
    html_content = re.sub(r'<h1 class="wiz-title">', '<h1>', html_content)
    # 类似处理其他标题级别
    return html_content
```

## 批量转换策略

### 文件发现和过滤

```python
def find_html_files(directory, recursive=True):
    """查找目录中的所有HTML文件"""
    html_files = []
    pattern = "**/*.html" if recursive else "*.html"
    
    for file_path in Path(directory).glob(pattern):
        # 跳过附件目录中的文件
        if "_files" not in str(file_path.parent):
            html_files.append(file_path)
    
    return html_files
```

### 并行转换优化

使用多进程加速批量转换：

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def batch_convert_parallel(html_files, output_dir, max_workers=None):
    """并行批量转换HTML文件"""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for html_file in html_files:
            md_file = output_dir / html_file.with_suffix('.md').name
            future = executor.submit(convert_single_file, html_file, md_file)
            futures[future] = html_file
        
        results = {'success': 0, 'failed': 0, 'errors': []}
        for future in as_completed(futures):
            html_file = futures[future]
            try:
                success = future.result()
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Failed {html_file}: {e}")
    
    return results
```

### 增量转换机制

避免重复转换已处理文件：

```python
def should_convert(input_file, output_file, force=False):
    """判断是否需要转换文件"""
    if not output_file.exists():
        return True
    if force:
        return True
    # 检查输入文件是否比输出文件新
    input_mtime = input_file.stat().st_mtime
    output_mtime = output_file.stat().st_mtime
    return input_mtime > output_mtime
```

## 错误处理和恢复

### 转换失败诊断

常见转换错误及解决方案：

#### 错误1：编码问题
**症状**：乱码或特殊字符显示异常
**解决**：
```bash
pandoc --from=html --to=markdown --encoding=utf-8
```

#### 错误2：内存不足
**症状**：转换大文件时崩溃
**解决**：
1. 增加系统内存
2. 分割大文件分批处理
3. 使用流式处理

#### 错误3：格式不兼容
**症状**：转换后格式混乱
**解决**：
1. 预处理HTML清理无效标签
2. 使用自定义过滤器
3. 调整转换参数

### 失败恢复策略

```python
def convert_with_recovery(html_file, md_file, max_retries=3):
    """带重试机制的转换"""
    for attempt in range(max_retries):
        try:
            success = convert_single_file(html_file, md_file)
            if success:
                return True
        except Exception as e:
            if attempt == max_retries - 1:
                log_error(f"Failed after {max_retries} attempts: {e}")
                return False
            # 等待后重试
            time.sleep(2 ** attempt)  # 指数退避
    
    return False
```

## 性能优化技巧

### 内存使用优化

1. **流式处理大文件**
   ```python
   def convert_large_file(input_path, output_path, chunk_size=1024*1024):
       """分块处理大文件"""
       # 实现分块读取和转换
       pass
   ```

2. **临时文件管理**
   ```python
   import tempfile
   
   with tempfile.TemporaryDirectory() as tmpdir:
       # 在临时目录中处理文件
       pass
   ```

### 速度优化

1. **并行处理**
   - 根据CPU核心数设置工作进程数
   - 合理分配文件到不同进程
   - 监控进程负载均衡

2. **缓存优化**
   - 缓存常用转换结果
   - 复用已处理的中间文件
   - 避免重复计算

### 磁盘I/O优化

1. **批量读写**
   ```python
   def batch_process_files(file_list, batch_size=100):
       """批量处理文件减少I/O开销"""
       for i in range(0, len(file_list), batch_size):
           batch = file_list[i:i+batch_size]
           process_batch(batch)
   ```

2. **异步I/O**
   ```python
   import asyncio
   
   async def async_convert_file(input_file, output_file):
       """异步转换文件"""
       # 异步文件操作
       pass
   ```

## 质量保证

### 转换验证

检查转换质量：

```python
def verify_conversion(html_file, md_file):
    """验证转换结果质量"""
    
    # 1. 文件存在性检查
    if not md_file.exists():
        return False, "Output file not created"
    
    # 2. 内容非空检查
    md_content = md_file.read_text()
    if len(md_content.strip()) == 0:
        return False, "Empty output"
    
    # 3. 基本格式检查
    if not contains_markdown_elements(md_content):
        return False, "No markdown elements found"
    
    # 4. 完整性检查（可选）
    html_stats = get_file_stats(html_file)
    md_stats = get_file_stats(md_file)
    
    # 简单的启发式检查
    if md_stats['size'] < html_stats['size'] * 0.1:  # 小于10%可能有问题
        return False, "Suspiciously small output"
    
    return True, "Verification passed"
```

### 抽样测试

随机抽样测试转换质量：

```python
def random_sample_test(html_files, sample_size=10):
    """随机抽样测试转换质量"""
    import random
    
    sample_files = random.sample(html_files, min(sample_size, len(html_files)))
    results = []
    
    for html_file in sample_files:
        # 执行转换和验证
        success, message = test_single_file(html_file)
        results.append({
            'file': html_file.name,
            'success': success,
            'message': message
        })
    
    return results
```

## 自定义扩展和配置

### 用户自定义过滤器

用户可以创建自定义过滤器：

```lua
-- custom_filter.lua
function Pandoc(doc)
  -- 自定义处理逻辑
  return doc
end
```

使用自定义过滤器：
```python
pandoc_args = DEFAULT_PANDOC_ARGS + ['--lua-filter=custom_filter.lua']
```

### 配置文件支持

支持外部配置文件：

```yaml
# pandoc_config.yaml
pandoc:
  default_args:
    - "--from=html"
    - "--to=markdown"
    - "--wrap=none"
  filters:
    - "remove_attrs.lua"
    - "custom_filter.lua"
  extensions:
    - "+emoji"
    - "+footnotes"
  output_options:
    encoding: "utf-8"
    line_ending: "lf"
```

加载配置：
```python
import yaml

def load_pandoc_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
```

### 插件系统

可扩展的插件架构：

```python
class PandocPlugin:
    """Pandoc插件基类"""
    def pre_process(self, html_content):
        """预处理钩子"""
        return html_content
    
    def post_process(self, md_content):
        """后处理钩子"""
        return md_content
    
    def get_pandoc_args(self):
        """获取Pandoc参数"""
        return []

# 使用插件
plugins = [WizNotePlugin(), MathPlugin(), ImagePlugin()]
pandoc_args = []
for plugin in plugins:
    pandoc_args.extend(plugin.get_pandoc_args())
```

## 监控和日志

### 转换统计

收集转换统计信息：

```python
class ConversionStats:
    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.total_time = 0
        self.file_sizes = {}
        self.errors = []
    
    def add_result(self, file_name, success, time_taken, error=None):
        self.total_files += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
            if error:
                self.errors.append((file_name, error))
        self.total_time += time_taken
    
    def get_summary(self):
        return {
            'total': self.total_files,
            'success': self.successful,
            'failure': self.failed,
            'success_rate': self.successful / self.total_files if self.total_files > 0 else 0,
            'avg_time': self.total_time / self.total_files if self.total_files > 0 else 0,
            'errors': self.errors
        }
```

### 性能监控

监控转换性能：

```python
import time
import psutil

def monitor_conversion(html_file, md_file):
    """监控单个文件转换性能"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    # 执行转换
    success = convert_single_file(html_file, md_file)
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss
    
    return {
        'file': html_file.name,
        'success': success,
        'time': end_time - start_time,
        'memory_used': end_memory - start_memory,
        'output_size': md_file.stat().st_size if md_file.exists() else 0
    }
```

### 日志系统

详细的日志记录：

```python
import logging

def setup_pandoc_logger(log_level=logging.INFO):
    """设置Pandoc转换日志"""
    logger = logging.getLogger('pandoc_converter')
    logger.setLevel(log_level)
    
    # 文件处理器
    file_handler = logging.FileHandler('pandoc_conversion.log')
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```