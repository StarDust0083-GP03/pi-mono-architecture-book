# 第 4 章：一次请求的完整生命周期

**本章目标：区分消息流、持久历史和模型输入。**

理解新版最有效的路线不是先读所有类，而是跟一条请求走到底。

1. CLI、SDK 或 RPC 收到输入。提示模板可先展开，扩展可以处理命令或变换输入。
2. `AgentSession` 负责运行准备、模型与工具配置、压缩检查、扩展生命周期和队列。
3. `SessionManager` 从当前叶子追溯活动分支，重建已定稿的上下文。
4. harness 组合系统提示、分支消息、工具声明和模型设置，交给 provider。
5. provider 产生流式事件，Agent 归一化为消息和回合事件。
6. 如果 assistant 请求工具，则校验、触发扩展钩子、执行，记录结果。
7. 如果还有工具结果或队列需要处理，则继续；否则进入最终收尾。

![请求、普通工具和 Code Mode 嵌套调用的时序](diagrams/request-sequence.svg)

图中省略流式 token 与多轮重试，保留了最重要的边界：**嵌套工具结果先回给脚本，而不是直接变成下一次模型输入。** [S7](#s7)、[S9](#s9)、[S10](#s10)

### 同一响应的并行，不等于 Code Mode

当前 Agent 的工具执行默认支持并行：先按顺序做调用前检查，再并行执行被允许的工具；完成事件按实际完成顺序发出，最终的工具结果消息仍按 assistant 源码中的调用顺序写入历史。需要共享状态的工具可以选择顺序执行。[S6](#s6)

这意味着：模型在一个响应里同时请求三次 `read`，不使用 Code Mode 也可能并行。Code Mode 多出的价值是**在一个脚本中表达依赖、分支、过滤与聚合**，并控制哪些结果跨回模型边界，而不只是“把串行变成并行”。

### 三种历史不要混淆

| 视角 | 保存或展示什么 | 用途 |
|---|---|---|
| 原始会话历史 | 消息、分支、压缩、上下文编辑、配置变化、自定义状态等 | 追溯、恢复、导出 |
| UI 和执行事件 | 流式输出、嵌套工具进度、完成时长等 | 观察正在发生什么 |
| 模型上下文投影 | 活动分支经过压缩、上下文编辑、消息转换后的输入 | 下一轮模型推理 |

当前 JSONL 条目通过 `id` / `parentId` 组成树。`/tree` 可以从旧节点继续，同时保留被放弃分支。压缩追加摘要和保留边界，而不是删除原始历史；`context_edit` 可以让某个历史条目在未来模型上下文中被省略或替换，但不重写其原始记录。[S11](#s11)

### 压缩和 Code Mode 各解决什么

默认压缩阈值的概念是：

```text
contextTokens > contextWindow - reserveTokens
```

Code Mode **在信息进入模型之前就做减量**；压缩则是在上下文已经积累后，把早期内容总结成摘要。前者不能替代后者。普通工具调用也可以先截断输出；Code Mode 更适合按数据含义做结构化筛选。[S12](#s12)

例如运行测试得到很长日志。工具截断保留头尾，不知道你只关心三个失败断言；脚本可从结构化结果中选出失败项，再让模型理解原因。但如果你把全部日志 `text()` 出去，就没有获得这部分上下文收益。

### v1.4.0：何时压缩，与摘要能输出多长是两回事

`compaction.reserveTokens` 仍决定自动压缩何时开始，但不再按它为摘要请求算一个固定输出上限。v1.3.0 的主摘要曾取 `floor(0.8 × reserveTokens)` 与模型输出上限中的较小者；当推理内容占用额度时，正文摘要可能还没写完就结束了。v1.4.0 改用模型输出上限，并在必要时让输入与输出共同适配上下文窗口。所以“移除固定上限”不表示输出无限，也不表示摘要一定成功。[S12](#s12)、[S28](#s28)

用教学数值手算：上下文窗口 128,000，预留 16,384，则超过 111,616 时触发自动压缩；旧主摘要按比例算出的上限约为 13,107。新版不会因为预留值相同，就把摘要仍然限制在 13,107。扩大预留值主要让压缩更早发生，不应再用它间接调整摘要长度。

分支总结也采用新输出预算。导出的 `generateSummary()` 和 `generateSummaryWithUsage()` 为兼容旧调用保留参数位置，但忽略原来的 `reserveTokens` 参数；维护自定义调用时要重新核对意图。`/compact 保留未解决问题` 之类指令也会传给被切开的回合前缀摘要，修复了此前这部分忽略指令的问题。

### v1.4.0：截断恢复后，工具消息仍要成对

模型在输出上限处被截断，可能留下不完整的工具调用。历史转换不能只丢掉调用请求，却把对应工具结果交给下一轮 provider；孤立结果会使后续请求持续被拒绝。v1.4.0 修复了这条恢复路径。此处说的是模型响应截断后的协议一致性，不是工具长输出被截断后的 JSON 解析问题。[S2](#s2)

### 什么时候才算真的结束

SDK 的 `agent_end` 只代表一次底层 Agent 运行结束，之后还可能发生自动恢复、重试或排队工作。集成程序要确认 Pi 不再自动继续，应该关注 **`agent_settled`**。把两者当成同一个事件，会导致 UI 过早解除忙碌状态，或者脚本过早退出。[S9](#s9)

**理解检查：** 从树中切回旧节点，会不会回滚已经写入的文件？不会。会话分支描述对话历史，不是文件系统快照。

# 第 5 章：Code Mode 到底改变了什么

**本章目标：能用一句话解释它，并知道何时不该使用。**

**让模型写一段调用工具的 JavaScript，常规编排在脚本中完成，只把主动输出的内容交还模型。**

普通工具模式下，工具编排分散在 assistant 的工具请求及其后续模型响应中。Code Mode 把部分编排移到程序执行侧，模型看到一个外层 `codemode` 调用，脚本内部可以调用很多工具。底层工具仍然是真实工具。[S10](#s10)

![普通工具与 Code Mode 的信息流比较](diagrams/information-flow.svg)

### 一个具体任务：检查三个 package.json

需求：“读取根目录、api 和 web 的 package.json，只告诉我包名与 scripts 里有没有 test。”

不用 Code Mode，模型可以请求三次 `read`，收下三个完整文件，再挑选字段；也可以请求 shell 直接聚合，或调用专门工具。Code Mode 不是唯一能做聚合的办法。

使用 Code Mode，可以表达为：

```js
const paths = [
  "package.json",
  "packages/api/package.json",
  "packages/web/package.json",
];

const rows = await Promise.all(paths.map(async (path) => {
  const raw = await tools.read({ path });
  const pkg = JSON.parse(raw);
  return { path, name: pkg.name, hasTest: Boolean(pkg.scripts?.test) };
}));
text(rows);
```

假设三个文件都是未截断的有效 JSON，脚本内部会拿到全部内容，模型只收到选出的字段。`read` 返回的是字符串，不应写成 `raw.output`。如果读的是超大文件，被工具截断后就可能不是有效 JSON；应换成专门读取并解析的工具，或通过受控 shell 生成少量结构化数据。Code Mode 不会自动修复上游工具截断。

### 把控制流也写进去

如果其中一个包不存在，上一段的 `Promise.all()` 会让整个表达式失败。读取多个独立来源时，更实用的版本是：

```js
const paths = ["package.json", "missing/package.json"];
const results = await Promise.allSettled(
  paths.map(async (path) => JSON.parse(await tools.read({ path })))
);
text(results.map((r, i) => r.status === "fulfilled"
  ? { path: paths[i], name: r.value.name }
  : { path: paths[i], error: String(r.reason) }
));
```

`Promise.allSettled()` 让失败和成功一起交给后续逻辑。它不是“忽略错误”，而是把错误变成你必须检查的数据。并发调用之间必须互不依赖，不能把“写文件”和“马上读取刚写的文件”随意放进同一个并发数组。

### 上下文收益怎么估算

下面只是示意，不是 Pi 性能测试。设有 N 个独立调用，每个原始结果 R 个字符，最终每项只需要 S 个字符。

```text
全部原样返回：约 N × R
脚本选择字段：约 N × S + 外层包装
```

若 N = 12、R = 20,000、S = 300，数据量从约 240,000 个字符变成约 3,600 个字符，再加脚本和结果包装。**字符不是 token**，也不是费用；实际还受工具定义、模型分词、缓存和输出限制影响。这个例子只说明“把不需要的数据留在执行侧”的价值。

### 哪些事不值得套一层脚本

只读一个短文件，直接 `read` 通常更简单；要跑整个项目测试，直接 `bash` 就可能够了；需要长时间重型计算，QuickJS 也不比专门程序合适。不要为了使用 Code Mode，把本来一行能讲清的请求改成难读程序。

**小结：** 它的核心不是模型会写代码，也不是并行本身，而是把“工具输出到模型上下文”之间增加了一个可编程的数据处理层。

# 第 6 章：拆开沙箱，看见真正的调用链

**本章目标：知道脚本在哪里运行，权限检查在哪里发生。**

普通 CLI 的 Code Mode 由两层组成：`packages/codemode` 提供通用沙箱；`coding-agent/src/extensions/codemode` 负责把它接到 Pi 的工具、会话、展示和模型运行时。前者没有 Pi 内部包依赖，因此也能脱离编码代理单独使用。[S13](#s13)

![主线程、worker、WebAssembly 与 QuickJS 的边界](diagrams/sandbox-boundary.svg)

### 从源码追一次 tools.read()

1. `tool.ts` 定义 `codemode` 工具、输入形式和模型可见说明。
2. executor 读取当前可调用工具 `ctx.tools`，把每个工具包装成沙箱能力。
3. 创建 `CodemodeSandbox`，设置 QuickJS WASM、worker 入口、内存限制和 worker 准入控制。
4. `execute()` 启动 worker，在独立 WASM 实例中创建新的 QuickJS VM。
5. VM 内的 prelude 暴露 `tools`、`text`、`image`、`console`、`store` / `load` 等接口，桥接函数藏在闭包中。
6. 脚本调用 `tools.read(...)`，消息经过 worker 桥返回主线程。
7. 主线程调用 **`ctx.executeTool()`**，进入参数校验及 `tool_call` / `tool_result` 钩子。
8. 结果被转换成脚本值，返回 VM；脚本选择性输出。
9. executor 关闭沙箱、处理状态写入、截断输出、保存图片、生成外层工具结果。

在 v1.4.0 的 `execute.ts` 中，关键语句仍是：

```ts
const outcome = await ctx.executeTool(tool.name, args, { signal: callSignal });
```

它解释了为什么“脚本里的工具调用”不是绕开工具链直接执行函数。已有扩展实现的拦截与权限确认仍然可以生效。不过 Pi **没有内置一套对每次调用逐一确认的默认权限系统**；这里说的是扩展钩子可以执行权限策略，不是默认已经有一层强制审批。[S14](#s14)、[S15](#s15)、[S25](#s25)

### 为什么不用 Node 的 eval

脚本里没有 Node API、文件系统、网络、模块加载和定时器。不能直接使用 `process`、`require`、`fetch` 或 `setTimeout`，需要访问外部世界就通过注入工具。`eval` / `Function` 即使存在，也只能在同一个 VM 里生成更多代码，不凭空获得宿主能力。

QuickJS 是解释器，编译为 WebAssembly 后运行在 worker。worker 避免一段同步死循环卡住 Pi 主线程；WASM 实例分离 VM 内存；能力注入限制脚本可以接触的接口。这是分层设计，不是一句“用了沙箱所以绝对安全”。

### 限制属于哪一层

| 层次 | 典型限制或职责 |
|---|---|
| 脚本源格式 | 第一行可选 `// @options:`；错误位置或非法字段会报错 |
| VM | CLI 每脚本 256 MiB 堆限制，无法分配时失败 |
| 宿主/worker | deadline、abort、worker 生命周期与数量限制 |
| 输出收集 | 16 Mi 字符及 100,000 个输出项目上限 |
| 模型结果格式化 | 默认约 10,000 输出 token 预算，超长保留头尾并保存完整文本 |
| 底层工具 | 参数、外部进程、远程调用、工具自身截断与超时 |
| 操作系统或容器 | 文件、进程、网络与凭据的真正权限边界 |

这些限额不能混用。256 MiB 是 CLI 集成的选择，不是所有独立沙箱部署的通用默认；Cloudflare 默认限制又不同。外层输出 token 预算也不是 VM 内存限制。[S10](#s10)、[S13](#s13)

### 一个危险的误解

```js
await tools.bash({ command: "某个有破坏性的命令" });
```

命令执行发生在工具能力背后，能接触什么取决于 Pi 进程或工具专属容器，不取决于 QuickJS 是否能直接读文件。需要强隔离时，应限制容器挂载、网络、账户和凭据；只限制 JavaScript 全局变量远远不够。

**源码阅读顺序：** `tool.ts` → `execute.ts` → `codemode/src/runtime/host.ts` → `worker.ts` → `vm.ts` → `prelude-source.ts`。先沿着一次调用走通，再研究声明生成和模型辅助接口。
