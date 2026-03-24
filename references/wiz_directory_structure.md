# 为知笔记目录结构详解

## 标准安装路径

### Windows 系统

```text
C:\Users\[用户名]\Documents\My Knowledge\
├── Data\                          # 主数据目录
│   ├── [邮箱账号1]\               # 用户账号目录
│   │   ├── index\                 # 笔记索引和元数据
│   │   │   ├── *.idx              # 索引文件
│   │   │   ├── *.jdb              # 数据库文件
│   │   │   └── *.log              # 日志文件
│   │   ├── attachments\           # 账号特定附件
│   │   │   ├── [日期]\            # 按日期组织的附件
│   │   │   │   └── [文件]
│   │   │   └── [GUID]\            # 按GUID组织的附件
│   │   └── notes\                 # 笔记内容文件
│   │       ├── [日期]\            # 按日期组织的笔记
│   │       └── *.ziw              # 笔记文件（ziw格式）
│   └── [邮箱账号2]\
│       └── ...                    # 其他账号类似结构
└── _Attachments\                  # 全局共享附件目录
    ├── [年份]\                    # 按年份组织的全局附件
    │   ├── [月份]\
    │   └── [文件]
    └── [特殊用途]\                # 特殊用途附件目录
```

### macOS 系统

```text
~/Documents/My Knowledge/         # 标准路径
或
~/Library/Application Support/WizNote/Data/  # 某些版本
```

### Linux 系统

```text
~/.wiznotes/                      # 常见路径
或
~/.local/share/wiznote/           # 某些发行版
```

## 数据文件格式说明

### 笔记文件 (.ziw)

为知笔记专有格式，实际是压缩的XML文件：

```
笔记标题.ziw
├── meta.xml                     # 笔记元数据
├── content.xml                  # 笔记内容（HTML格式）
├── attachments.xml              # 附件引用信息
└── [附件文件]                   # 嵌入的附件
```

### 索引文件格式

- `*.idx` - 主索引文件，记录笔记ID、标题、标签等
- `*.jdb` - JET数据库文件，存储结构化数据
- `*.log` - 操作日志文件

## 附件存储策略

### 1. 账号特定附件

存储位置：`Data/[账号]/attachments/`

特点：
- 与特定用户账号关联
- 按上传日期或GUID组织
- 通常位于原始笔记文件同一目录下

### 2. 全局共享附件

存储位置：`_Attachments/`

特点：
- 跨账号共享使用
- 按年份/月份组织
- 集中管理，避免重复存储

## 导出时的附件处理

### HTML导出格式

当使用"多个网页文件（含附件）"格式导出时：

```text
导出目录/
├── 笔记本名称/
│   ├── 笔记标题.html            # HTML格式笔记
│   └── 笔记标题_files/          # 同名附件目录
│       ├── image001.png         # 图片文件
│       ├── document.pdf         # 文档文件
│       └── ...                  # 其他附件
└── ...                         # 其他笔记本
```

### 附件映射关系

原始位置 → 导出位置：

```text
Data/[账号]/attachments/[日期]/image.png
↓ 导出时复制到 ↓
笔记标题_files/image.png
```

## 迁移注意事项

### 路径识别要点

1. **相对路径 vs 绝对路径**
   - 导出后的HTML使用相对路径引用附件
   - 需要在迁移后保持相对路径有效性

2. **附件命名规范**
   - 为知笔记使用GUID或时间戳命名附件
   - 导出时可能重命名为更具可读性的名称

3. **目录深度限制**
   - 为知笔记可能限制目录深度
   - 导出时可能扁平化部分目录结构

### 特殊附件类型

1. **内嵌附件**
   - 部分版本将小附件直接嵌入.ziw文件
   - 导出时会提取为独立文件

2. **外部链接**
   - 可能包含指向外部资源的链接
   - 迁移时需要特别处理

3. **加密附件**
   - 某些企业版支持附件加密
   - 需要相应权限才能访问

## 存储结构检测算法

参考 `scripts/detector.py` 中的检测逻辑：

```python
def detect_wiz_data_dir():
    """检测为知笔记数据目录"""
    possible_paths = [
        # Windows 标准路径
        r"C:\Users\%USERNAME%\Documents\My Knowledge\Data",
        # macOS 标准路径
        os.path.expanduser("~/Documents/My Knowledge/Data"),
        # Linux 标准路径
        os.path.expanduser("~/.wiznotes/Data"),
        # 其他可能路径
        os.path.expanduser("~/.local/share/wiznote/Data"),
    ]
    
    for path in possible_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            # 进一步检查是否为有效为知笔记目录
            if is_valid_wiz_directory(expanded_path):
                return expanded_path
    
    return None
```

## 常见配置变体

### 自定义安装路径

用户可能自定义安装位置，检测时需要：
1. 检查Windows注册表路径
2. 查看环境变量配置
3. 扫描常见自定义位置

### 多版本共存

不同版本可能使用不同目录结构：
- 个人版 vs 企业版
- 旧版本 vs 新版本
- 本地版 vs 云同步版

### 网络存储配置

企业部署可能使用网络存储：
- 网络共享目录
- 云存储同步
- 分布式文件系统