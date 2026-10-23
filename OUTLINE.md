# 研究提纲与证据映射

目标：按照现有课程的章节、源码追踪、图解和练习方式，制作一部中文架构电子书，不把最新主分支混入固定发布比较。

## 章节与依据

1. 版本歧义与时间线：GitHub 发布 API、固定标签、变更日志。
2. 旧版架构：v0.9.4 Agent、transport、ai 中的循环、SessionManager。
3. 新版包与运行时：v1.4.0 包清单、Agent 文档、How Pi Works。
4. 请求生命周期与状态：SDK、session-format、compaction、extension 契约。
5. Code Mode 工作模型：用户文档、独立包文档、字段筛选实例。
6. 沙箱内部：executor、tool.ts、host/worker/VM/prelude、声明生成。
7. 发现与 MCP：MCP、settings、exposure、reachesTools。
8. 错误与状态：结果适配、store 提交、取消与 worker 准入。
9. 扩展与接口：扩展、SDK、CLI、模型辅助 API、TUI/RPC。
10. 最近版本差异：0.99.2 到 1.4.0 的 scoped diff，以及 1.3.0 到 1.4.0 增量与多个包的变更日志。
11. 独立、远程、持久：Code Mode 的 portable/start/remote、Durable journal、pi-env。
12. 迁移与实验：官方 SDK 示例、CLI 参数、模拟工具脚本和检查题。

## 图解

共 12 张：旧新分层对照、旧运行链、当前运行时、真实 CLI 包依赖、请求时序、信息流、沙箱边界、工具发现、分支 store、部署方式、Durable 重放、Durable/env 包依赖。所有图使用中文说明、模块名保持原文；静态 SVG 同时适配网页、PDF 和 EPUB。

## 事实边界

- 0.9.x 与 0.99.x 分开比较。
- Code Mode 从 0.99.0 已经内置，不归为 1.0 才出现。
- 普通 CLI 与实验性 Durable 不混画成同一套内核。
- 独立 Code Mode 包在 0.99.2 已存在；最新区间新增 remote/start 等能力。
- 失败不提交 store，不代表撤销外部副作用。
- 源码实验目录删除，不等于正式 CLI 运行链整体替换。
- 示意字符量、上游测量和本地验证分别标明。
- v1.4.0 的 worker 等待计入总 deadline；脚本名额与脚本内模型调用并发分开。
- reserveTokens 控制压缩触发，不再限制摘要输出；图片分类需按 provider 核对协议。

## 验证

模拟工具脚本、来源文件存在性、内部链接和唯一 ID、SVG 可访问性及标签边界、桌面和移动端渲染、交互演示、PDF 页与图、EPUB XML/ZIP/资源/目录。未做项目全量测试、正式 EPUBCheck、真实云部署或安全审计。
