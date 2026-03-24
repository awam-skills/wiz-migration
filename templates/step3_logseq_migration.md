# 步骤 3: Logseq 导入与附件修复

本步骤将帮助你把转换好的 Markdown 文件迁移到 Logseq 图谱，并修复附件路径。

## Logseq 图谱准备

### 打开 Logseq 图谱
1. 启动 Logseq
2. 打开你的图谱（Graph）
3. 进入图谱设置：

```
Logseq → 设置 → 图谱 → 打开图谱文件夹
```

### 确认目录结构
你的图谱目录应该包含：
```
你的图谱/
├── pages/       # 存放页面文件（Markdown 放这里）
├── journals/    # 日记文件
└── assets/      # 所有附件统一放这里
```

## 迁移流程

### 步骤 1: 收集附件到 assets/
程序会自动：
- 扫描所有 `xxx_files/` 文件夹
- 复制所有附件到 Logseq 的 `assets/` 目录
- 同名文件会自动添加 `wiz_` 前缀避免覆盖

### 步骤 2: 移动 Markdown 到 pages/
- Markdown 文件会被移动到 `pages/` 目录
- 如果有同名文件，会自动重命名

### 步骤 3: 修复附件路径
程序会自动：
- 将 Markdown 中的 `xxx_files/` 路径替换为 `../assets/`
- 替换示例：
  ```
  原: ![图片](笔记1_files/abc.png)
  改: ![图片](../assets/abc.png)
  ```

## 注意事项

1. **同名文件处理**: 如果 `assets/` 中已有同名文件，程序会自动重命名为 `wiz_xxx`
2. **备份建议**: 建议先备份你的 Logseq 图谱
3. **分层目录**: 如果你需要按原笔记本分类组织文件，可以指定子目录

## 路径替换说明

Logseq 的页面在 `pages/` 目录，附件在 `assets/` 目录。
从 `pages/` 下的文件引用 `assets/` 需要使用 `../assets/` 路径。

这就是为什么我们替换为 `../assets/` 而不是 `/assets/`。