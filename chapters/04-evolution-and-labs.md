# 第 10 章：从 0.99.2 到 1.4.0，具体差了什么

**本章目标：把长期演进、1.3.0 基线和 1.4.0 增量分开。**

如果你的“0.9.xxx”其实是 0.99.2，前面很多机制你已经有了：Code Mode、独立 `pi-codemode` 包、工具发现、MCP、树形会话、统一扩展，并不是升级到 1.4.0 才第一次出现。下面只看这个较短区间。[S2](#s2)、[S21](#s21)

| 版本 | Code Mode 及相关架构变化 | 对使用者的影响 |
|---|---|---|
| 1.0.0 | 缩短模型可见说明，增加错误恢复提示；加入 `models.generateImages()` | 工具脚本提示更小，可以生成图像；探测工具是否存在要用 `in` |
| 1.0.0 | 从 `pi-agent-core` 移除实验性 AgentHarness 与相关导出 | 依赖旧实验 API 的 SDK 使用者必须迁移，普通 CLI 不因此换内核 |
| 1.0.1 | 输出硬上限，防无限 `text()` 撑爆宿主；MCP 项目覆盖等 | 输出也受资源治理，不能只关心 VM 内存 |
| 1.0.3 | `image()` 同时保存临时图片文件 | 后续回合可复制和引用图片路径 |
| 1.0.4 | 内建对象冻结；读图返回图片块；MCP 工具过滤规则修复 | 不可依赖修改 Array 等原型；图片可从 read 传给 image |
| 1.1.0 | CLI `--tools +name/-name`；发现 helper 的异步说明；输出项目分隔 | 增量启用工具更方便，多段结果更容易识别 |
| 1.2.0 | 声明显示 schema 约束；`reachesTools`、命名空间 aliases；MCP 解耦 | 工具编排器可替换，不必绑定特定内置实现 |
| 1.2.0 | 远程/inline 沙箱、portable 入口、确定性 `sandbox.start()` | 独立包可部署到 Cloudflare，给持久重放提供基础 |
| 1.2.0 | Durable 加入可恢复的 Code Mode；删除 CLI 未发布服务端实验栈 | 需要恢复的应用有新路径，但不可照旧实验目录继续开发 |
| 1.3.0 | 取消结果不等待实际退出；按真实 worker 生命周期限制容量 | timeout 更及时，重复取消不会无上限积累 worker |
| 1.3.0 | 恢复会话时保留活动工具；内部 Pi 依赖固定到精确版本 | 恢复后的工具集更一致，减少混装不同内部版本 |
| 1.4.0 | worker 满时排队，最多等待 60 秒；可调整全进程 worker 上限 | 并行脚本不再立即因容量不足失败，等待仍消耗总 deadline |
| 1.4.0 | 压缩及分支摘要使用模型输出上限 | `reserveTokens` 只决定压缩触发时机，不再间接限制摘要长度 |
| 1.4.0 | 图片分类输入、provider 分类器兼容字段、配置字段参考 | 可用结构化问题检查图片，但要核对模型能力、协议与费用 |
| 1.4.0 | 截断工具消息、晚注册扩展工具与并发弹窗修复 | 恢复后消息和工具更一致，交互 Promise 不再被新弹窗遗留 |

### 从 v1.3.0 升到 v1.4.0，优先验哪四件事

1. 在隔离测试进程中占满 worker，再发新脚本，观察它等待后启动或到期失败；检查等待时间是否计入总 deadline。
2. 用支持推理的模型执行长会话压缩，确认没有继续将 `reserveTokens` 当摘要长度旋钮；对分割回合检查自定义摘要指令。
3. 对图片分类保留“无可用模型”“服务失败”“仅文字模型”反例，不把 Promise fulfilled 当业务成功。
4. 从旧会话恢复、切换树形分支并加载扩展，核对活动工具；注入模型输出截断后核对工具请求与结果仍然配对。

这些是集成验收建议，不是本轮全部已运行的测试。1.4.0 的 Rex 终端支持、退出模式清理、Linux 挂起后的剪贴板和中文标点旁 Markdown 渲染也有改善，但没有改变前面所画的 Agent / AgentSession / Code Mode 职责分层。[S2](#s2)

### “约少 40% token”到底指什么

v1.0.0 变更日志给出的例子是：默认工具并启用 Code Mode 时，一个 GPT-5.6 请求的提示规模从约 5,300 降到约 3,300 token。减少来自说明精简、按需阅读模型 API 文档、避免重复声明等。它是上游记录中的特定场景，不是本书实测，更不是任何项目、模型、工具数量下都少 40%。[S2](#s2)

### 三个明确的迁移断点

**探测工具存在性。** 新版访问未知成员可能抛出带近似匹配建议的错误。旧代码 `typeof tools.someName` 也可能触发属性读取，改用 `"someName" in tools`。[S21](#s21)

**MCP 类型声明。** 独立包在 v1.2.0 移除了 `MCP_TYPESCRIPT_PREAMBLE` 和 `mcpStructuredContentSchema()`。输出 schema 直接描述完整返回对象，声明渲染不再依赖一个悬空的 `CallToolResult<T>` 名称。消费这些底层导出的应用要更新。[S21](#s21)

**独立沙箱 close()。** v1.3.0 中结果和 `close()` 在请求关闭后即可 settle，不代表 worker 已退出。自己管理资源池时，用 `onWorkerStarted(exited)` 或 `acquireWorker()` 的释放回调追踪真实退出，不能照旧按结果完成释放容量。[S13](#s13)、[S21](#s21)

### 不要继续照旧实验目录做设计

v1.0.0 的 `pi-agent-core` 清理与 v1.2.0 的 CLI 实验栈清理是两件事。前者确实移除了该包的旧实验性 harness 导出；后者移除的 client/protocol/server 栈未进入正式 coding-agent 发布包。做源码研究时能看见它们，不能据此假设它们都是稳定产品 API。[S18](#s18)、[S22](#s22)

# 第 11 章：独立沙箱、云端执行与 Durable 重放

**本章目标：分清三个看似相近、恢复保证完全不同的架构。**

“Code Mode 可以恢复”这句话缺少主语。普通 CLI、独立沙箱库、Durable 扩展提供的保证并不相同。

| 形态 | 谁拥有工具与状态 | 中途崩溃后怎样处理 |
|---|---|---|
| 普通 CLI Code Mode | AgentSession 与扩展 | 已成功提交的小型 store 可恢复；没有普通脚本指令级自动续跑保证 |
| 独立 `CodemodeSandbox.execute()` | 你的宿主 | 你自己管理持久化；一次执行不自动变持久任务 |
| `sandbox.start()` | 宿主驱动的确定性 VM | 提供可重放机制，宿主仍需日志与调度 |
| 实验性 `pi-durable/codemode` | Durable Harness、存储、任务与 journal | 重启后重放已记录结果并继续；未完成外部调用服从各自 replay 策略 |

### 11.1 不用整个 Pi，也能用沙箱

独立 `pi-codemode` 的核心接口是注入工具、执行脚本、读取结构化执行结果。工具函数在宿主执行，VM 只保留受限 JavaScript 环境。[S13](#s13)

```ts
import { CodemodeSandbox } from "@earendil-works/pi-codemode";

const sandbox = new CodemodeSandbox({
  timeoutMs: 10_000,
  tools: [{
    name: "lookup",
    execute: async ({ id }) => ({ id, title: `条目 ${id}`, privateNote: "不输出" }),
  }],
});

try {
  const result = await sandbox.execute(`
    const row = await tools.lookup({ id: 7 });
    text({ id: row.id, title: row.title });
  `);
  if (!result.ok) throw new Error(result.error.message);
  console.log(result.output);
} finally {
  await sandbox.close();
}
```

这是独立库示例，直接注入自己的可信函数。若要套进现有 Agent，不能因为省事直接调用原始 `tool.execute()`，把既有验证和钩子绕过。官方 CLI 走 `ctx.executeTool()`；低层 Agent 应使用相应工具调用管线。[S13](#s13)

### 11.2 为什么 Cloudflare 要把 VM 放进另一个 Worker

Node/Bun 用 worker thread 把计算隔离出主线程。Cloudflare 没有同样的 Node worker 环境，且 QuickJS 同步计算会阻塞承载它的 isolate。

v1.2.0 新增 `RemoteCodemodeSandbox`：工具和调用记录留在会话一侧，VM 放到**单独部署的 Worker 中的 Durable Object**，每次工具调用通过 Workers RPC 回到宿主。这里的 Durable Object 是 Cloudflare 基础设施，不等于 `pi-durable` 包。[S13](#s13)、[S21](#s21)

![三种沙箱部署方式](diagrams/deployment.svg)

上游 README 记录了特定 Cloudflare 测试：让脚本持续计算十秒，放在会话对象内或由它加载的 Dynamic Worker 会延迟其他会话请求约十秒，单独部署的 Worker 则约为 50 ms。该数字是上游环境测量，用来说明部署边界选择，不承诺本地环境或你的账号相同。

Cloudflare 还有两个限制要单独理解：计算不 yield 时墙钟 timeout 不足以约束 CPU，使用 interrupt budget；远程 abort 可以先结束调用侧等待，VM 在下一次工具调用或耗尽预算时才停。远程默认每 VM 32 MiB，不能套用普通 CLI 的 256 MiB。

`InlineCodemodeSandbox` 直接在调用线程运行，适合能接受阻塞的宿主。portable 入口不包含 Node imports，方便这些环境共用同一脚本 API。

### 11.3 Durable 恢复的是执行历史，不是 VM 内存快照

`pi-durable` 在 v0.99.2 的仓库中已经存在，最新区间新增的是与确定性脚本重放结合的 Code Mode 等能力。它是实验 API，版本间可随时变化。Harness 把会话条目、文档状态、任务和提交放进存储，提交后才发布相关状态；持久任务保存阶段检查点，重启后继续调度。[S23](#s23)

![Durable Code Mode 的记录、重放与继续](diagrams/durable-replay.svg)

运行脚本时：

1. 固定虚拟时钟、随机种子、时区和 VM 指纹等条件。
2. 脚本发出嵌套工具调用，工具本身成为 Durable 任务。
3. 宿主在把结果交给 VM 之前，将结果与顺序写入 journal。
4. 进程崩溃后重新运行脚本，按原来顺序喂入记录的结果。
5. 脚本因此发出相同调用，按 key 重新关联已完成或仍在运行的任务，再继续新的工作。

`sandbox.start()` 的确定性约束包括：`Date.now()` 来自宿主提供的时间、随机性来自 seed、固定 UTC、不暴露 WeakRef/FinalizationRegistry、结果按宿主编号应用。它不要求保存整个 QuickJS 堆快照。[S13](#s13)、[S23](#s23)

### 一个“扣款后崩溃”的边界案例

假设工具向外部系统发起扣款，外部扣款成功，但本地还没记录结果就崩溃。重启后能否再次调用？不能靠“脚本可以重放”来决定。Durable 工具只有声明 `replay: "safe"` 才能在中断后重新执行；否则会产生 interrupted 错误。即便声明 safe，外部副作用仍需服务端幂等 key 或查询确认。[S23](#s23)

所以它并不提供跨任意外部服务的“恰好一次副作用”魔法。它提供的是可记录、可检查、可恢复的调度和调用关系。代码路径改变、VM 指纹或 Code Mode 版本变化，以及 deadline 已经过期，都可能令重放报错，而不是盲目继续。

### 11.4 远程执行环境解决另一个问题

`pi-env` 把 Durable 工具的文件与命令操作转到远端机器：本地保留 Harness、存储和凭据；通过 SSH 启动小型 Rust daemon，运行协议化文件与进程操作。`RemoteExecutionEnv` 尽量保持与 `NodeExecutionEnv` 相同的语义。[S24](#s24)

这与把 QuickJS VM 放远端是两个独立选择：VM 放哪里，决定脚本计算在哪里；执行环境放哪里，决定文件和命令在哪里发生。远程执行也不自动成为沙箱，仍要限制远端账户权限、网络和可用凭据，核验 SSH host key。

![Durable、Code Mode、模型层与远程执行环境的实际包关系](diagrams/durable-package-dependencies.svg)

这张图与第 3 章的 CLI 依赖图应分开阅读：一个是实验性持久执行方案，一个是普通编码代理。它们复用模型和沙箱基础库，不意味着生命周期、状态格式和恢复契约相同。

# 第 12 章：迁移路线与动手实验

**本章目标：把概念变成能检查的操作，不在读完后只记得名词。**

### 12.1 从 v0.9.4 迁移，先选你实际使用的层

如果只是使用终端 CLI，备份会话与配置、确认新包名和运行环境，再逐步开启功能。当前 README 要求 Node.js 22.19 或更新；不要把旧仓库根目录的 Node 20 要求当作现版本要求。

如果嵌入的是旧 `Agent`，重点检查 transport API 到当前 `streamFn` / 消息转换接口的变化、旧附件模型、事件与并发语义。不要只替换 npm 包名就假定类型兼容。若依赖旧 `AgentHarness`，当前 `pi-agent-core` 已不再导出它，需要明确迁向 `AgentSession` 还是实验性 Durable。[S6](#s6)、[S22](#s22)

如果自定义过 hooks 与 tools，按当前 extension API 合并注册位置，并根据事件的准确返回类型处理阻止、变换与通知。不要把早年事件名机械替换成新名字而不检查契约。

### 12.2 从 v0.99.2 迁移，做一张小检查表

- [ ] 识别工具存在性用 `"name" in tools`，不靠读取未知成员。
- [ ] 发现 helper 全部有 `await`。
- [ ] shell 判断退出码，MCP 判断 `isError`。
- [ ] options 行确实在脚本第一行。
- [ ] 需要保存的图片调用 `image()`，不把 base64 当文本输出。
- [ ] 自定义沙箱资源池按真实 worker 退出释放容量，排队不重置总 deadline。
- [ ] `reserveTokens` 按触发阈值配置，不继续当摘要输出帽子。
- [ ] 图片分类核对 `input`、provider 图片协议、错误结果与 usage。
- [ ] 自定义编排器声明正确的 `reachesTools`。
- [ ] 旧 experimental harness 或 server/client 导出没有继续被引用。
- [ ] 恢复会话后验证活动工具与过滤策略，不仅看启动命令。
- [ ] SDK 明确添加需要的内置扩展并绑定生命周期。

### 12.3 在不改安装的情况下阅读本次下载

以下命令核对本机保留的研究副本；公开电子书不附完整 Git 目录。其他读者可先下载本版源码 ZIP，或按固定标签准备自己的副本。

```sh
# 在电子书仓库根目录执行。

git -C sources/pi-v1.4.0 describe --tags --exact-match
# v1.4.0

# 上一版参照仍保留：
git -C sources/pi-mono describe --tags --exact-match
# v1.3.0

git -C sources/pi-v0.9.4 describe --tags --exact-match
# v0.9.4

git -C sources/pi-v0.99.2 describe --tags --exact-match
# v0.99.2
```

`pi-mono-v1.4.0.zip` 是不包含依赖与 Git 历史的源码快照，方便离线拷贝。安装依赖或更新全局 Pi 是独立操作，本次没有执行。

### 实验 A：开启 Code Mode，但保留默认工具

在确认安装版本支持这些参数后，可运行：

```sh
pi --tools +codemode
```

或将下面字段**合并**到项目 `.pi/settings.json`，不要直接覆盖已有文件：

```json
{
  "defaultTools": ["+codemode"]
}
```

请模型读取几个小文件并只返回选中字段，观察一个外层 Code Mode 调用和多个嵌套调用。对比要求它把每个完整文件都输出时的结果大小。这里测试的是信息选择，不是证明任何固定 token 节省比例。

### 实验 B：不用模型，测试相同脚本的控制流

本书提供 `examples/run-checks.mjs`，使用 Node 内置断言和模拟工具运行脚本文件：

```sh
node examples/run-checks.mjs
```

它检查并行读取与字段筛选、部分失败保留、非零 shell 退出码、成功/失败状态提交，图片分类的成功与失败契约，以及输出减量算术。它不是 QuickJS 的安全测试，不调用外部服务，也不能证明 MCP 或真实沙箱无缺陷。Code Mode 脚本放在 `examples/scripts/`，可以阅读或交给 Pi 使用。

### 实验 C：观察分支与外部世界的区别

在临时项目里执行一个脚本，保存小游标并写入测试文件。回到保存前的会话节点创建另一分支，再 `load()`：游标沿新分支重建，但文件不会因此恢复。只使用可丢弃文件，不要拿生产数据做这个实验。

### 实验 D：按官方 SDK 示例接上 MCP

`examples/sdk-codemode-mcp.ts` 是固定版本官方示例的副本。重点阅读三处：`extensionFactories` 安装三个内置扩展；`defaultTools` 增量启用；`session.bindExtensions({})` 发出启动事件。真正运行需要当前包、凭据和 MCP 配置。本次没有自动执行付费模型调用或添加服务器。

### 五个问题，检查是否真的理解

1. **Code Mode 是否等于多个工具并行？** 不等于。新版普通调用也能并行；Code Mode 多了程序控制流和中间结果筛选。
2. **脚本失败，之前写文件会撤销吗？** 不会。成功才提交的小 store 与外部文件写入没有统一事务。
3. **MCP Promise fulfilled 是否意味着成功？** 不意味着。还要检查 `isError`。
4. **普通 CLI 恢复会话是否会从脚本中断的语句继续？** 没有这个通用保证。Durable Code Mode 通过日志和确定性重放提供另一种恢复机制。
5. **QuickJS 没有文件系统，shell 就安全吗？** 不能这样推断。注入工具背后的权限才决定影响范围。

### 常用词，放回各自的位置

| 词 | 在本书中的含义 |
|---|---|
| Agent loop | 模型响应、工具执行、下一轮判断的循环 |
| Harness | 循环外围的上下文、状态、资源和生命周期设施 |
| AgentSession | 普通编码代理中拥有会话及运行状态的对象 |
| Turn | 一次模型响应及其工具调用 |
| Run | 一次输入引发的一个或多个回合及收尾 |
| Exposure | 工具如何被模型看见、如何被其他工具调用 |
| Loadout | 当前声明和可调用工具的配置视图 |
| Nested call | 由工具内部发起、结果先返回调用者的调用 |
| Projection | 从持久历史构建出的模型可见上下文 |
| QuickJS / WASM | JavaScript 引擎及其在沙箱中的运行载体 |
| Journal / replay | 记录已交付结果，再按确定顺序重放 |
| Idempotency | 重试同一业务操作不重复产生不可接受副作用的契约 |

### 接下来沿源码读哪几处

从普通 CLI 入手，先读 `how-pi-works.md` 和 `sdk.md`，再读 Code Mode 文档、`tool.ts` 与 `execute.ts`。想把脚本能力放进自己的产品，优先读独立 `codemode/README.md`。只有确实需要跨重启任务恢复，再进入 Durable 的 README 和规范，不要一开始就把实验 runtime 当作必要前置。

所有图都按职责做了适度简化。各模块内部的重试、流式事件和 schema 细节应回到下一节的固定版本来源核对。
