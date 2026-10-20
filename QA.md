# 构建验证记录

日期：2026-10-20。发布版本：v1.3.0（GitHub latest release 与 npm latest 均为 1.3.0）。

## 通过

- `node examples/run-checks.mjs`：5 个教学脚本；字段筛选、部分失败、shell 退出码、成功/失败 store 提交、外部写入不回滚、示意算术。
- `python3 verify_book.py`：12 章、12 个可访问 SVG、无重复 ID、章节锚点、本地链接、EPUB XML/ZIP/manifest/导航、源码 ZIP 版本、PDF 头。
- EPUBCheck 5.2.1：EPUB 3.3，0 fatal / 0 error / 0 warning。
- 12 张 SVG 通过 `diagram-design/scripts/self_check.py`；无文字越界。
- 桌面 1440px 与移动 390px 渲染；无页面级横向溢出。移动端图为可横向滚动的 680px 最小宽度，避免文字缩小到不可读。
- 交互滑块：12 × 20,000 → 3,600 字符；60 × 20,000 → 18,000 字符。
- PDF：44 页，A4，包含打印目录、代码、表格和全部图。

## 未执行

- 上游完整测试套件。
- 用付费模型或真实 MCP 服务器运行 Code Mode。
- Cloudflare Worker、Durable Object、SSH / pi-env 部署。
- 沙箱安全审计或权限绕过测试。
- 用多种商业电子书阅读器逐页检查 EPUB；结构用 EPUBCheck 验证，视觉仍可能因阅读器字体和分页不同而变化。

## 复现命令

```sh
python3 make_diagrams.py
python3 build_book.py
java -jar epubcheck.jar pi-architecture.zh-CN.epub
node examples/run-checks.mjs
python3 verify_book.py
```

PDF 由 Chromium 从本地 `index.html` 打印。构建脚本不会访问网络，也不会修改当前 Pi 安装或配置。
