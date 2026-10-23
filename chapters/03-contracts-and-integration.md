# 第 7 章：工具太多时，怎样发现而不塞满提示

**本章目标：分清“注册”“向模型声明”和“可被脚本调用”。**

常见思路是把所有工具的名称、说明和参数 schema 都放进模型请求。工具少时这样做很直观；但面对几十个服务、几百个工具，它会撑大提示、干扰模型选择，工具集的变动还会波及缓存。

Pi 把这几件事拆开了：工具可以已注册却不直接声明给模型，可以供脚本调用却不出现在 Code Mode 说明里，也可以按需搜索后再声明。**不可见不等于不可用，也不等于权限已被撤销。** [S16](#s16)、[S17](#s17)

![直接声明、脚本发现和工具搜索三条路径](diagrams/discovery.svg)

### MCP 的四种 exposure

| MCP exposure | 默认向模型声明？ | 脚本可调用？ | 常见用途 |
|---|---|---|---|
| `direct` | 是，受当前工具选择约束 | 是 | 少量高频工具 |
| `codemode` | 否，默认也不列入 Code Mode 描述 | 是 | 大多数服务，先发现再组合 |
| `deferred` | 否；`tool_search` 可加载声明 | 是 | 希望发现后按普通工具直接调用 |
| `hidden` | 否 | 否 | 保留注册信息但使其不可达 |

MCP 默认使用 `codemode`。普通扩展工具还有 `model-only`，适合仅让模型直接调用、禁止其他工具间接调用的编排器或问答工具。不要把 MCP 配置表和扩展底层表机械合并：MCP 集成会处理命名空间和延迟发现，最终可达性还取决于禁用、过滤与活动集合。[S15](#s15)、[S16](#s16)

### 四个发现入口，各做一件事

```js
const hits = await searchTools("search documentation", { limit: 3 });
text(hits);
```

- `ALL_TOOLS`：当前可调用目录，包含名称和说明。
- `searchTools(query, options)`：BM25 相关性排序，找候选。
- `describeTool(name)`：获得某个工具的说明与 TypeScript 声明。
- `describeNamespace(name)`：读某个命名空间的指令和工具信息。

三个查询 helper 都是异步接口，调用时必须 `await`。BM25 做的是文本检索，并不理解业务语义；搜索词和工具说明写得如何，会直接影响结果质量。发现之后要先确认参数，不能猜个名字就直接调用。[S10](#s10)

示意流程如下，其中 `hits[0]` 只是候选，必须读完说明再决定是否合适：

```js
const hits = await searchTools("read documentation page", { limit: 3 });
if (hits.length === 0) return "没有找到候选工具";
text(await describeTool(hits[0].name));
```

发现结果会在这一轮交还模型，模型下一轮再据此编写准确的调用。发现和执行不必都挤在同一个脚本里。

### codemode.mode 的 on 与 only

`on` 是默认模式：已声明的工具继续直接可见，同时附带脚本调用提示。`only` 则隐藏这些底层工具的直接声明，把调用入口集中到 Code Mode；但可调用的集合本身不会因为声明被隐藏而消失。

```json
{
  "defaultTools": ["+codemode"],
  "codemode": { "mode": "on", "inlineBudget": 3000 }
}
```

`inlineBudget` 是对声明文本的 token 预算估计，大约按字符数除以四折算，并非精确分词。超出预算的工具交给发现接口查找。当前默认的 MCP 工具本就不会逐个写进 Code Mode 描述。`only` 属于呈现和编排策略，不提供更强的 OS 沙箱隔离。[S17](#s17)

### 为什么 MCP 不阻塞每次启动

从 v0.99.2 起，非 direct 服务器不再阻塞首个 prompt，而是先在后台连接；等到脚本点名某个服务器，或需要搜索全部工具时，再等待相关连接完成。当前用 `reachesTools(input)` 描述编排器可能触及哪些工具或命名空间，MCP 扩展据此等待必要的服务器。搜索整个目录意味着可能触及全部工具，所以要等更多服务就绪。[S2](#s2)、[S15](#s15)、[S16](#s16)

v1.2.0 将 MCP 与 Code Mode 解耦，意义也在这里：MCP 不再到处硬编码去“识别某个内置实现”，而是通过通用工具契约判断编排器的可达范围。替换同名编排工具时，需要一并提供相应的 `reachesTools` 契约。

### 一个容易造成权限误判的 CLI 细节

```sh
pi --tools read,codemode
```

在当前版本中，这条命令**不会自动删除 MCP 工具**，它们仍可能被脚本调用。要去掉 MCP，用 `--no-mcp`；按 MCP 名称筛选用 `mcp__` 模式；排除工具用 `--exclude-tools`。不能只读 allowlist 的表面含义，就当成完整的权限审计。[S16](#s16)、[S19](#s19)

# 第 8 章：结果、失败、并发与状态

**本章目标：写出在真实失败中仍然可理解的脚本。**

Code Mode 最容易写错的地方在返回值和失败契约，而不是语法。不要假定所有调用都返回字符串，也不要假定失败一定以 throw 的形式出现。

### 三种常见结果

| 工具 | 脚本通常拿到什么 | 需要检查什么 |
|---|---|---|
| `read` 读文本 | 字符串 | 是否被截断，是否符合预期格式 |
| `bash` | `{ output, exit_code, truncated, full_output_path?, ... }` | `exit_code`，即使 Promise fulfilled 也可能执行失败 |
| MCP 工具 | `CallToolResult`，包括 `content`、`structuredContent`、`isError` | `isError` 与实际字段，不要只读第一条文本就宣布成功 |

声明了 output schema 的工具可以把结构化值交给脚本，错误结果也可能携带结构化值。校验失败、被拦截、没有对应数据等执行异常可以 reject。MCP 会保留完整的结果对象，所以 `isError` 必须显式检查。最终以发现接口返回的声明和该工具的契约为准。[S10](#s10)、[S14](#s14)、[S16](#s16)

```js
const result = await tools.bash({ command: "npm test" });
if (result.exit_code !== 0) {
  text({ passed: false, tail: result.output.slice(-4000) });
} else {
  text({ passed: true });
}
```

对 MCP，下面仅表达检查方式，工具名和参数都是教学占位，需先用发现接口确认：

```js
// 伪代码：先发现真实工具，不要原样运行。
const result = await tools.mcp__docs__search({ query: "session" });
if (result.isError) throw new Error(JSON.stringify(result.content));
text(result.structuredContent ?? result.content);
```

### 两个层次的成功

`Promise.allSettled()` 返回 fulfilled，只说明 Promise 没有 reject，既不说明 shell 退出码为零，更不说明业务成功。可靠脚本会先看 Promise 状态，再看结果里的错误标志或退出码。

类似地，独立沙箱 `sandbox.execute()` 遇到脚本错误时通常返回 `{ ok: false, error }`，而不是直接 reject。脚本、宿主调用和模型 API 处在不同层次，错误表示并不通用。

### await 是生命周期的一部分

```js
// 错误示例：脚本可能先结束，未完成调用会被取消。
tools.read({ path: "package.json" });
return "完成";
```

```js
// 正确示例：确认依赖工作已完成。
const source = await tools.read({ path: "package.json" });
text(JSON.parse(source).name);
```

脚本结束时，尚未完成的调用会被请求取消；已经完成的外部副作用不会回滚。`Promise.all()` 因为其中一项失败而提前 reject，也可能让外层脚本结束，进而取消其他仍在进行的调用。彼此独立的读取适合用 `allSettled()`，有依赖关系的操作则按顺序执行。

### store 不是数据库事务

`store(key, value)` / `load(key)` 保存小型 JSON 状态。CLI 只有脚本成功后，才把变更追加为 `codemode-store` 自定义会话条目；恢复和树形分支都只重放当前路径上的状态。单值 JSON 长度上限为 262,144 字符，总量为 1,048,576 字符。[S10](#s10)、[S14](#s14)

![分支相对的脚本状态，与外部文件副作用的区别](diagrams/branch-store.svg)

```js
const count = (load("inspected") ?? 0) + 1;
store("inspected", count);
text({ count });
```

如果脚本后面 throw，状态写入不会提交；但此前通过 `write` 修改的文件可能已经变更。所以“失败不提交 store”并不等于“失败回滚整个脚本”。同理，在分支 A 保存的游标不会自动出现在从更早节点分出的分支 B 中，而文件系统对两者仍是同一份现实。

适合存：查询游标、选中的 ID、短摘要。不要存大型日志、图片 base64、完整仓库文件；大数据应由文件或外部服务承载。

### 取消不代表 worker 已经退出

CLI 默认最多允许同一 Pi 进程中两个 Code Mode worker 存活，跨会话共享；v1.4.0 可以用环境变量 `PI_CODEMODE_MAX_WORKERS` 指定正整数上限，非法值回退到默认 2。Bun 下，某些不轮询中断的内建操作可能在返回取消结果后继续运行，直到该操作结束。v1.3.0 的修复把“对用户立即返回取消”和“实际 worker 退出后释放名额”拆开，避免重复取消积累残留 worker。[S2](#s2)、[S13](#s13)、[S14](#s14)

这个区别很通用：**响应完成、任务停止、资源回收完成，是三个不同时间点。** 不能在 timeout 返回的瞬间就把并发名额无条件释放。

### v1.4.0：容量用尽时先排队，不是立即失败

v1.3.0 引入真实 worker 数量限制，但名额满时会立即拒绝新脚本。v1.4.0 的 `reserveCodemodeWorker()` 先把等待者加入队列；`admitCodemodeWorkers()` 按到达顺序放行，`releaseCodemodeWorker()` 在实际释放后继续准入。[S26](#s26)

等待最多 60 秒，并且计入脚本整体的 `timeout_ms`。假设脚本总时限 10 秒，排队花掉 8 秒，剩下最多只能执行约 2 秒，不会在拿到名额后再补一份完整的 10 秒。等待超时或被取消的请求会从队列移除；没有获得名额就不会启动 VM。

“两个 worker”并不等于“脚本里只能并发两个工具”。脚本中彼此独立的工具调用不会逐项占用这两个名额；`models.classify()` 和 `models.generateImages()` 另有每脚本最多 4 项在途调用的限制。调高 worker 上限会增加潜在的内存与外部调用压力，并不等于免费提升吞吐。

排队也不等于解决所有相互等待：脚本持有 worker，又等同进程中的另一个脚本获取名额，仍可能形成资源等待。60 秒等待上限提供失败出口，不提供无限递归子代理能力；脚本不能直接启动另一个 `codemode`。

### 四类常见错误的处置

| 症状 | 先检查什么 | 合理恢复 |
|---|---|---|
| `tools.X` 不存在 | 拼写、标识符规范、工具是否可达 | 重新发现并描述工具，不反复猜名字 |
| JSON.parse 失败 | 是否读到截断输出、日志或错误页面 | 换结构化工具或缩小读取内容 |
| 等待空闲 worker 超时 | 全进程名额、残留 worker、相互等待和总 deadline | v1.4.0 已自动排队；先查占用，不做高频重试 |
| 超时或部分成功 | 哪些调用已产生副作用 | 查明实际状态，再决定是否重试；写操作需幂等策略 |

# 第 9 章：扩展、模型与界面，哪些没被 Code Mode 替代

**本章目标：知道新增功能应该放在哪一层。**

定制需求并不都由 Code Mode 承担。模型生成的短程序编排归它；安装到 harness 的可执行行为归扩展；按需指令归 skill；复用输入归提示模板；配色归主题。这些能力彼此互补。

### 扩展：从分散机制到一个入口

v0.35.0 把 hooks 与自定义工具统一成 extensions，并把文件式 slash commands 改称 prompt templates，避免和真正注册的命令混淆。当前 TypeScript 扩展工厂接收 `ExtensionAPI`，可以注册工具、命令、事件处理器、模型提供商、渲染器等。[S2](#s2)、[S15](#s15)

最小例子：

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("hello", {
    description: "显示问候",
    handler: async (name, ctx) => {
      ctx.ui.notify(`你好，${name || "世界"}`, "info");
    },
  });
}
```

扩展直接运行在 Pi 进程中，能够接触文件、凭据与会话，不受 QuickJS 脚本那组全局变量限制。加载不可信扩展，比阅读一份不可信文档具有更直接的执行风险。

### 生命周期与状态放置

扩展工厂负责注册，不宜直接启动 watcher、socket、定时器。因为有些命令只加载扩展，并不启动会话。长寿命资源应在 `session_start` 或实际需要时开启，并在 `session_shutdown` 幂等清理。

分支相关工具状态可以放工具结果 `details`；不进入模型的持久数据用 `appendEntry()`；希望进入模型的自定义内容用 `sendMessage()`；跨会话数据用外部存储。重建状态应读取 `getBranch()`，不是遍历整个文件把其他分支也合并。[S15](#s15)

### Provider 仍然承担协议适配

Code Mode 不会消除 Anthropic、OpenAI、Google 等协议差异，模型接入、流式归一化与内容转换仍由 `ai` 层负责。v1.3.0 起切换模型时会丢弃由另一模型产生的历史 thinking 块，避免它们被当作普通文本交给新模型；特定提供商的缓存保持也属于 provider 相关行为，不能据此认为所有模型切换都没有代价。[S2](#s2)

脚本中的 `models.*` 可访问模型目录、运行分类器、生成图片，但不能把聊天模型当作任意子 Agent 在脚本中调用。分类和生成图片可能计费，其 usage 会纳入会话成本；要检查 `stopReason` 与 `errorMessage`。图片要用 `image(block)` 展示，不要用 `text()` 打印 base64。[S10](#s10)

### v1.4.0：把图片交给分类器，而非打印 base64

`models.classify()` 新增了 `images` 输入，适用于受支持的 Jev、Clef 服务以及具备相应能力的模型。模型类别是 classifier，并不代表它就支持图片：先查目录中的 `input` 是否包含 `"image"`，再按 provider 核对格式与数量限制。图片分类与生成图片是两项不同的能力。[S10](#s10)、[S27](#s27)

下面是 `examples/scripts/06-classify-image.js` 的契约示例。实际运行需要可用的图片分类模型、对应凭据和本地 `screenshot.png`，可能产生费用：

```js
const candidates = await models.getAvailableOfType("classifier");
const vision = candidates.find(m => m.input?.includes("image"));
if (!vision) throw new Error("没有可用的图片分类器");
const photo = await tools.read({ path: "screenshot.png" });
if (photo.type !== "image") throw new Error("需要图片块");
const result = await models.classify(vision, {
  state: { task: "检查页面布局" },
  images: [photo],
  questions: {
    broken: {
      type: "bool",
      instructions: "图片中是否有重叠或被截断的内容？",
      criteria: { true: "存在布局缺陷", false: "未发现布局缺陷" },
    },
  },
});
if (result.stopReason !== "stop") {
  throw new Error(result.errorMessage ?? result.stopReason);
}
const answer = result.answers.broken;
if (answer?.type !== "bool") throw new Error("分类回答类型不符");
text({ probability: answer.probability });
```

`probability` 是模型判断的概率，不是经过本书验证的页面缺陷率，也不能证明图片没有问题。本书仅用替身检查调用结构、错误处理和不输出图片内容，没有调用真实分类服务。

代理兼容尤其需要注意：各 System One 服务接收图片的格式不同。`compat.imageInput` 和 `sendImageOptInHeader` 可在 provider 层配置；直接把请求改发 OpenRouter，却继续使用 TypeSafe 的 assets 形态，可能出现请求成功但图片被忽略。v1.4.0 新增的 `models-configuration.md` 从 schema 生成字段参考，按实际代理协议查证，不猜兼容选项。[S29](#s29)

### 恢复会话与扩展弹窗也有边界修复

v1.3.0 已能恢复分支记录过的活动工具；v1.4.0 进一步处理工具注册晚于分支记录的情况，例如会话开始后才安装的扩展。分支没有显式增删的工具默认可活动，但 `defaultActive: false` 仍应生效。恢复之后要检查实际可调用的集合，不能把这项修复理解成强制启用所有工具。

交互式扩展同时打开 `select`、`confirm`、`input`、`editor` 或 inline `custom()` 时，新弹窗不再让先前 Promise 永久悬挂；关闭当前弹窗会回到前一个。这修的是交互生命周期，不是给扩展增加 OS 权限隔离。[S2](#s2)

### 选择哪种集成方式

| 需要 | 优先接口 | 注意事项 |
|---|---|---|
| 人在终端中交互 | TUI | v1.0.0 起默认全屏，可切回 regular |
| 一次性自动化 | `--print` | 一次运行后退出 |
| 消费事件流 | `--mode json` | stdout 为 JSONL 协议 |
| 非 TypeScript 宿主长期控制 | RPC | stdin 命令，stdout 响应和事件 |
| Node/Bun 应用内嵌 | SDK | 宿主负责生命周期、资源和事件绑定 |
| 只想执行受限工具脚本 | 独立 `pi-codemode` | 不必引入整个编码代理 |
| 需要持久任务恢复 | 实验性 `pi-durable` | 独立 API、存储与重放策略 |

TUI 是事件消费者和交互层，不是业务循环本身。RPC 与 SDK 不需要另写一套 Agent 算法，它们驱动的是同一套 session/agent 机制。自定义 UI 要区分 `ctx.hasUI` 与终端专属组件，不能假定 print 模式下也有确认框。[S7](#s7)、[S9](#s9)、[S15](#s15)

### SDK 的一个关键差异

CLI 会加载内置 Code Mode、tool-search、MCP 扩展；SDK 默认不会替你装好这三者。需要通过 `DefaultResourceLoader.extensionFactories` 添加，并在建立会话后 `bindExtensions()`，让 `session_start` 触发 MCP 后台连接。本书 `examples/sdk-codemode-mcp.ts` 保存了该版本官方示例。[S20](#s20)

**设计练习：** “每次调用 shell 前做企业策略校验”应该写进临时的 Code Mode 脚本吗？不应该。可审计的扩展策略应当实现在工具边界，真正的权限边界则用 OS/容器限制补上。模型生成的代码不是执行强制安全策略的合适位置。
