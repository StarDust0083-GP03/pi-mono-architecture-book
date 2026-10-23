# Pi 架构演进中文电子书

比较 **v0.9.4 / v0.99.2 → v1.4.0**，保留 v1.3.0 为上一版参照，重点解释 Code Mode、工具执行、MCP、会话和实验性 Durable 的区别。

## 阅读入口

- [网页版电子书](index.html)：中文目录、完整正文、12 张 SVG 图、交互式信息量演示。
- [PDF](pi-architecture.zh-CN.pdf)：A4 排版、可点击目录与来源链接。
- [EPUB](pi-architecture.zh-CN.epub)：可导入支持 EPUB 3 和 SVG 的电子书阅读器。
- [Markdown 原稿](book.zh-CN.md)：便于编辑、搜索和再次排版。
- [本版源码 ZIP](https://github.com/StarDust0083-GP03/pi-mono-architecture-book/releases/download/book-v1.4.0/pi-mono-v1.4.0.zip)：固定标签 v1.4.0，不含安装依赖和 Git 历史。

网页的正文、图片和阅读样式均保存在文件中，不依赖网络加载才能阅读；初始化模板保留了可选 Tailwind CDN，断网也有完整本地样式回退。EPUB 没有外部资源依赖。

## 内容

共 12 章，覆盖：

1. 0.9.x 与 0.99.x 的区别和版本时间线。
2. v0.9.4 的 Agent、transport、工具循环和线性会话。
3. 当前 CLI、AgentSession、包职责和实际依赖。
4. 请求生命周期、树形会话、上下文投影与压缩。
5. Code Mode 的信息处理模型及前后对照。
6. QuickJS、WASM、worker、宿主桥和工具钩子。
7. MCP、exposure、工具发现与按需连接。
8. 返回值、错误、并发、取消和分支相对 store。
9. 扩展、模型、TUI、RPC 与 SDK。
10. v0.99.2 到 v1.4.0 的变化、1.3 到 1.4 增量和迁移断点。
11. 独立沙箱、Cloudflare、确定性重放、Durable 与 pi-env。
12. 迁移清单、实验、练习答案和术语。

## 架构图清单

`diagrams/` 中同时提供可独立打开的 SVG：

- `architecture-comparison.svg`：旧版与新版分层对照。
- `old-stack.svg`：v0.9.4 运行链。
- `current-stack.svg`：当前普通 CLI 运行时。
- `cli-package-dependencies.svg`：普通 CLI 真实内部包依赖。
- `request-sequence.svg`：Code Mode 调用时序。
- `information-flow.svg`：普通调用与脚本筛选的区别。
- `sandbox-boundary.svg`：主线程、worker、VM、工具边界。
- `discovery.svg`：工具发现与 exposure。
- `branch-store.svg`：分支状态与外部副作用。
- `deployment.svg`：Node/Bun、Cloudflare、inline 部署。
- `durable-replay.svg`：journal、确定性重放与继续。
- `durable-package-dependencies.svg`：Durable、env、chord 和共享基础库。

## 源码与证据

核查日期：2026-10-23。本版固定 **v1.4.0**（正式发布时间为 2026-10-21），不跟随标签之后的主分支。新增 worker 排队、摘要预算、图片分类与恢复边界说明。

- `sources/pi-v1.4.0/`：新增的独立 worktree，固定在 v1.4.0。
- `sources/pi-mono/`：上一版源码，仍固定在 v1.3.0。
- `sources/pi-v0.9.4/`、`sources/pi-v0.99.2/`：同仓库的独立 Git worktree。
- `sources/versions.json`：发布 API 返回值与四个固定提交。
- `sources/source-index.json`：29 条官方来源，正文使用 S1 至 S29 编号。
- `sources/*--stat.txt`、`sources/*--name-status.txt`：完整文件级差异。

没有修改原来的 `../pi-mono/`，没有更新全局 Pi，没有改任何 Pi 用户配置，没有安装或运行源码依赖。

## 教学脚本与检查

```sh
node examples/run-checks.mjs
python3 verify_book.py
```

检查只使用 Node 模拟工具验证教学脚本，不是沙箱安全测试。6 个教学脚本含图片分类成功与失败契约。`examples/sdk-codemode-mcp.ts` 与 v1.4.0 官方 SDK 示例一致，运行它需要另外准备依赖、凭据与服务器。

再生成 Markdown、网页与 EPUB：

```sh
python3 make_diagrams.py
python3 build_book.py
```

`build_book.py` 使用本机已存在的 `markdown_it`。PDF 用 Chromium 从网页打印，命令示例：

```sh
chromium --headless --disable-gpu --no-pdf-header-footer \
  --timeout=10000 \
  --print-to-pdf="$PWD/pi-architecture.zh-CN.pdf" \
  --user-data-dir=/tmp/pi-ebook-print \
  "file://$PWD/index.html"
```

构建与检查的实际范围见 [QA.md](QA.md)。未运行完整上游测试、付费模型、实际 MCP、Cloudflare 或 SSH；EPUBCheck 的本次运行结果见 QA.md。
