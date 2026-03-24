# 步骤4：HTML 转换为 Markdown

完成附件迁移后，现在将 HTML 笔记转换为 Markdown 格式。

## 转换方案

提供两种转换方案：

### 方案 A：Pandoc 转换（推荐）

- **优点**：转换质量高，格式保留好
- **依赖**：Pandoc（跨平台文档转换工具）
- **自动安装**：支持 Windows (winget/chocolatey/scoop)、macOS (Homebrew)、Linux (apt/dnf/yum)

### 方案 B：Python html2text（备选）

- **优点**：纯 Python 实现，无需安装额外系统级软件
- **依赖**：html2text 库
- **自动安装**：pip install html2text

## 附件引用说明

为知笔记导出的笔记结构：
```
Wiz_Export/
├── 笔记1.html
├── 笔记1_files/
│   ├── image1.png
│   └── attachment.pdf
└── 笔记2.html
```

转换后 Markdown 中的图片引用格式：
```markdown
![image](笔记1_files/image1.png)
```

请确保 `xxx_files/` 目录与对应的 `.md` 文件在同一目录下。

## 操作说明

1. 选择转换方案（A：Pandoc，B：html2text）
2. 输入导出目录路径
3. 确认开始转换
4. 等待转换完成

## 常见问题

**Q: 转换后图片不显示？**
A: 检查 `xxx_files/` 目录是否与 `.md` 文件在同一位置，以及 Markdown 中的路径引用是否正确。

**Q: Pandoc 安装失败？**
A: 可以选择方案 B 使用 html2text 进行转换。

**Q: 转换失败怎么办？**
A: 检查 HTML 文件是否损坏，或尝试使用另一种方案。
