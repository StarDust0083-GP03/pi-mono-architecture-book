# 构建验证记录

日期：2026-10-23。本版源码端点：v1.4.0，固定提交 `4a080252f06caf63a525d7873c5d94d3c23887e0`；保留 v0.9.4、v0.99.2 和 v1.3.0 的对照。

## 通过

- `node examples/run-checks.mjs`：6 个教学脚本；字段筛选、部分失败、shell 退出码、成功和失败的 store 提交、外部写入不回滚、示意算术，以及图片分类的成功、服务错误、无图片模型和缺失回答反例。
- `python3 verify_book.py`：12 章、12 个可访问 SVG、唯一 ID、章节锚点、本地链接、EPUB XML/ZIP/manifest/导航、v1.4.0 源码 ZIP 版本及完整性、版本说明、来源入口和教学代码一致性、PDF 头。
- EPUBCheck 5.2.1：EPUB 3.3，0 fatal / 0 error / 0 warning。
- 浏览器检查全部 12 张 SVG，无文字越出画布。架构对照图标注同步为 v1.4.0，其余职责图保持原有结构。
- 桌面 1440px 与移动 390px 渲染；新增 worker 排队小节和表格可读，无页面级横向溢出。移动端图保留可横向滚动的最小宽度。
- PDF：49 页，A4。由 Chromium 重新打印，并用 `pdftotext` 核对 v1.4.0、worker 上限、摘要预算、图片分类和 S29 来源等新增内容。
- SDK 示例与 v1.4.0 上游的 `14-codemode-mcp.ts` 逐字节一致。

## 未执行

- 上游完整测试套件，包括真实 worker 准入和压缩集成测试。
- 用付费模型、实际图片分类器或真实 MCP 服务器运行示例。
- Cloudflare Worker、Durable Object、SSH / pi-env 部署。
- 沙箱安全审计或权限绕过测试。
- 用多种商业阅读器逐页检查 EPUB。EPUBCheck 验证结构，不保证各阅读器的字体与分页一致。

图片分类检查使用 Node 中的替身，只证明教学脚本的调用结构和错误处理，不证明真实分类质量、费用或 provider 兼容性。PDF/EPUB 的本轮构建与当前 Pi 的安装、配置无关。

## 复现命令

```sh
python3 make_diagrams.py
python3 build_book.py
node examples/run-checks.mjs
java -jar /tmp/epubcheck/epubcheck-5.2.1/epubcheck.jar pi-architecture.zh-CN.epub
python3 verify_book.py
```

PDF 需在构建 HTML 后使用 README 中的 Chromium 命令重新打印。`build_book.py` 本身不生成 PDF，也不访问网络或修改当前 Pi 安装。
