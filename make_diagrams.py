"""生成本书的静态 SVG 教学图，无外部渲染器。"""
from pathlib import Path
from html import escape

OUT = Path(__file__).parent / 'diagrams'
OUT.mkdir(exist_ok=True)
INK, MUTED, PAPER, ACCENT = '#20201d', '#6b6a64', '#faf9f5', '#1B365D'


def diagram(slug, title, desc, nodes, edges, height=480, labels=(), zones=()):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" role="img" aria-labelledby="{slug}-title {slug}-desc">',
             f'<title id="{slug}-title">{escape(title)}</title>', f'<desc id="{slug}-desc">{escape(desc)}</desc>',
             f'<defs><marker id="{slug}-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{ACCENT}"/></marker></defs>',
             f'<rect width="960" height="{height}" fill="{PAPER}"/>']
    for x, y, w, h, name in zones:
        parts += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{MUTED}" stroke-dasharray="6 5"/>',
                  f'<text x="{x+16}" y="{y+27}" font-size="17" fill="{MUTED}">{escape(name)}</text>']
    for path, dashed in edges:
        parts.append(f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="2" {"stroke-dasharray=\"6 5\"" if dashed else ""} marker-end="url(#{slug}-arrow)"/>')
    for x, y, w, h, title_lines, sub in nodes:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}" stroke="{ACCENT}" stroke-width="1.5"/>')
        for i, line in enumerate(title_lines):
            parts.append(f'<text x="{x+w/2}" y="{y+30+i*26}" text-anchor="middle" font-size="20" fill="{INK}">{escape(line)}</text>')
        if sub:
            parts.append(f'<text x="{x+w/2}" y="{y+h-15}" text-anchor="middle" font-size="15" fill="{MUTED}">{escape(sub)}</text>')
    for x, y, label in labels:
        parts.append(f'<text x="{x}" y="{y}" font-size="18" fill="{MUTED}">{escape(label)}</text>')
    parts.append('</svg>')
    result = ''.join(parts).replace('<svg ', '<svg style="font-family:Noto Sans CJK SC,system-ui,sans-serif" ', 1)
    (OUT / f'{slug}.svg').write_text(result)


def n(x,y,title,sub='',w=240,h=88):
    return (x,y,w,h,title.split('|'),sub)


diagram('old-stack', 'v0.9.4 的职责分层', '编码应用装配有状态 Agent 与 transport，ai 包内的循环调用模型和工具，SessionManager 保存线性日志。', [
    n(360,28,'编码应用','coding-agent/main.ts'), n(360,156,'有状态 Agent','agent/src/agent.ts'),
    n(360,284,'Transport → 工具循环','loop 位于 ai 包'), n(40,284,'工具执行','校验后顺序执行'),
    n(680,284,'模型提供商','统一流式接口'),n(680,28,'SessionManager','线性 JSONL / 复制分支')
], [('M480 116 V156',False),('M480 244 V284',False),('M360 328 H280',False),('M600 328 H680',False),('M600 72 H680',False)],
    height=440,labels=[(40,414,'旧版已有工具校验、事件流和分支；还没有当前这一套 Code Mode 内置扩展。')])

diagram('current-stack', '普通 CLI 的运行时地图', '接口进入 AgentSession，后者使用树形会话、Agent 循环和扩展工具，Code Mode 是工具侧编排层。', [
    n(360,24,'TUI / JSON / RPC','或应用内 SDK'), n(360,148,'AgentSession','上下文、队列、扩展生命周期'),
    n(40,148,'SessionManager','活动分支、压缩、投影'),n(680,148,'资源与模型运行时','设置、skills、providers'),
    n(120,276,'Agent 循环','packages/agent'),n(600,276,'工具执行管线','校验与扩展钩子'),
    n(120,404,'模型提供商','packages/ai'),n(600,404,'Code Mode / MCP','内置扩展及独立库')
], [('M480 112 V148',False),('M360 192 H280',False),('M600 192 H680',False),
    ('M420 236 V248 Q420 256 412 256 H248 Q240 256 240 264 V276',False),
    ('M540 236 V248 Q540 256 548 256 H712 Q720 256 720 264 V276',False),
    ('M240 364 V404',False),('M720 364 V404',False)],height=540)

# 时序图用水平消息，时间向下。
slug='request-sequence'
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 640" role="img" aria-labelledby="{slug}-title {slug}-desc" style="font-family:Noto Sans CJK SC,system-ui,sans-serif">',
       f'<title id="{slug}-title">一次 Code Mode 请求</title><desc id="{slug}-desc">模型请求脚本，脚本经宿主工具管线调用真实工具，结果回给脚本筛选，再向模型返回摘要。</desc>',
       f'<defs><marker id="{slug}-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{ACCENT}"/></marker></defs>',
       f'<rect width="960" height="640" fill="{PAPER}"/>']
for x,name in [(100,'模型'),(350,'AgentSession'),(600,'QuickJS 脚本'),(850,'工具管线')]:
    parts += [f'<rect x="{x-90}" y="24" width="180" height="56" rx="6" fill="none" stroke="{ACCENT}"/>',
              f'<text x="{x}" y="59" text-anchor="middle" font-size="19">{name}</text>',
              f'<path d="M{x} 80 V610" stroke="{MUTED}" stroke-dasharray="5 5" fill="none"/>']
for x1,x2,y,label,dashed in [(100,350,140,'请求 codemode',False),(350,600,204,'启动脚本',False),(600,850,268,'tools.read()',False),
                           (850,600,332,'原始工具结果',True),(600,350,396,'text(选定字段)',True),(350,100,460,'外层工具结果',True),(100,350,540,'下一轮响应',False)]:
    parts += [f'<path d="M{x1} {y} H{x2}" stroke="{ACCENT}" stroke-width="2" {"stroke-dasharray=\"6 5\"" if dashed else ""} fill="none" marker-end="url(#{slug}-arrow)"/>',
              f'<text x="{(x1+x2)/2}" y="{y-12}" text-anchor="middle" font-size="18" fill="{INK}">{label}</text>']
parts.append('</svg>')
(OUT / f'{slug}.svg').write_text(''.join(parts))

diagram('information-flow','把信息处理移到执行侧','普通工具结果直接供模型理解；Code Mode 在执行侧组合并筛选，只交回选中输出。',[
    n(30,76,'模型选择工具',w=180),n(270,76,'真实工具',w=180),n(510,76,'原始结果',w=180),n(750,76,'模型筛选',w=180),
    n(20,300,'模型写脚本',w=160),n(210,300,'脚本发调用',w=160),n(400,300,'真实工具',w=160),n(590,300,'脚本筛选',w=160),n(780,300,'模型读摘要',w=160)
],[('M210 120 H270',False),('M450 120 H510',False),('M690 120 H750',False),
   ('M180 344 H210',False),('M370 344 H400',False),('M560 344 H590',True),('M750 344 H780',False)],height=456,
labels=[(30,40,'普通调用：结果进入模型后，由模型理解与挑选'),(30,260,'Code Mode：保留原始数据在执行侧，选中输出才进入模型'),(30,436,'两种方式都可以并行；区别主要是控制流与信息跨界的位置。')])

diagram('sandbox-boundary','脚本如何跨过宿主桥','脚本在 worker 中的 QuickJS/WASM 运行，工具调用经消息桥到主线程，再进入验证与扩展钩子；真实能力在工具一侧。',[
    n(70,100,'工具适配器','ctx.executeTool',w=240),n(70,300,'校验与扩展钩子','真实工具执行',w=240),
    n(390,100,'worker 消息桥','JSON 请求与结果',w=220),n(680,100,'QuickJS / WASM','脚本、prelude、受限全局',w=240),
    n(680,300,'脚本输出','text / image / return',w=240)
],[('M680 144 H610',False),('M390 144 H310',False),('M190 188 V300',False),('M800 188 V300',False)],height=480,
labels=[(40,450,'无直接文件系统/网络 ≠ 注入的 bash 没有宿主权限。')],zones=[(40,40,300,380,'Pi 主线程'),(370,40,570,380,'worker 与独立 VM')])

diagram('discovery','工具发现的三条路径','注册表中的工具可直接声明、经脚本发现调用，或由 tool_search 声明后直接调用；hidden 工具不可达。',[
    n(360,30,'工具注册与 exposure','不是全部塞入提示'),
    n(40,190,'direct','模型直接可见'),n(360,190,'codemode','脚本发现后调用'),n(680,190,'deferred','按需加载声明'),
    n(40,350,'普通工具调用'),n(360,350,'searchTools / describe','结果先返回脚本'),n(680,350,'tool_search','下一请求可直接调用')
],[('M420 118 V140 Q420 148 412 148 H168 Q160 148 160 156 V190',False),('M480 118 V190',False),
   ('M540 118 V140 Q540 148 548 148 H792 Q800 148 800 156 V190',False),
   ('M160 278 V350',False),('M480 278 V350',False),('M800 278 V350',False)],height=500,
labels=[(40,478,'MCP 的 codemode 与 deferred 都可被脚本调用；hidden 在两条间接路径中也不可达。')])

diagram('branch-store','状态沿分支重放，外部文件不会回滚','从早期节点分叉时不继承另一路上的 store 写入，但文件系统副作用独立于会话分支。',[
    n(40,176,'共同历史','store: inspected = 1'),n(360,64,'分支 A 成功','store: inspected = 2'),
    n(680,64,'继续 A','load 得到 2'),n(360,288,'分支 B','从共同历史分出'),n(680,288,'继续 B','load 得到 1')
],[('M280 208 H312 Q320 208 320 200 V116 Q320 108 328 108 H360',False),
   ('M280 240 H300 Q308 240 308 248 V324 Q308 332 316 332 H360',False),('M600 108 H680',False),('M600 332 H680',False)],height=468,
labels=[(40,432,'若 A 已写入外部文件，切回 B 不会把文件恢复到过去。失败脚本不提交 store，但副作用也不撤销。')])

diagram('deployment','相同脚本 API，不同计算位置','Node/Bun 用 worker thread，Cloudflare 可把 VM 放在单独 Worker 的 Durable Object，inline 模式在调用线程运行。',[
    n(40,64,'Node / Bun 宿主','工具与 deadline',w=300),n(600,64,'worker thread','QuickJS VM',w=300),
    n(40,224,'Cloudflare 会话侧','工具与调用记录',w=300),n(600,224,'单独部署的 Worker','Durable Object 中的 VM',w=300),
    n(40,384,'Inline 宿主','允许计算阻塞调用线程',w=300),n(600,384,'同一线程的 VM','interrupt budget',w=300)
],[('M340 108 H600',False),('M340 268 H600',False),('M340 428 H600',False)],height=520,
labels=[(380,88,'线程消息'),(380,248,'Workers RPC'),(380,408,'直接调用')])

diagram('durable-replay','确定性重放，不是 VM 内存快照','首次运行先记录工具结果再交给脚本；重启后用相同代码环境和结果顺序重放，再继续新的调用。',[
    n(30,72,'相同代码与环境','seed、虚拟时间、指纹',w=260),n(350,72,'首次运行','发出嵌套任务',w=260),n(670,72,'先记录再交付','结果写入 journal',w=260),
    n(30,300,'进程重启','恢复 Harness 与任务',w=260),n(350,300,'重新运行脚本','按序喂回已记录结果',w=260),n(670,300,'关联已有调用并继续','未完成工具服从 replay 策略',w=260)
],[('M290 116 H350',False),('M610 116 H670',False),('M290 344 H350',False),('M610 344 H670',False),('M800 160 V264 Q800 272 792 272 H488 Q480 272 480 280 V300',True)],height=480,
labels=[(30,440,'外部副作用仍要幂等；普通 CLI 的一次脚本执行没有自动获得这些恢复保证。')])

diagram('architecture-comparison','旧版与新版的分层对照','旧版 Agent 经 transport 使用 ai 包中的循环；新版 AgentSession 管理会话，agent 包拥有循环，ai 专注模型接入。',[
    n(70,80,'编码应用','旧版 main / TUI',w=320),n(70,240,'Agent + Transport','状态与传输抽象',w=320),n(70,400,'ai：循环与模型接入','工具循环在 ai 包内',w=320),
    n(570,80,'AgentSession / 资源 / 扩展','树形会话与上下文投影',w=320),n(570,240,'agent：Agent 与工具循环','通用嵌套调用契约',w=320),n(570,400,'ai：多提供商模型接入','流式事件与公共消息类型',w=320)
],[('M230 168 V240',False),('M230 328 V400',False),('M730 168 V240',False),('M730 328 V400',False)],height=568,
labels=[(70,40,'v0.9.4'),(570,40,'v1.4.0 普通 CLI'),(70,540,'Code Mode 接在新版工具侧；Durable 不在这条普通 CLI 运行链中。')])

diagram('cli-package-dependencies','普通 CLI 的实际内部包依赖','coding-agent 直接依赖 agent-core、ai、tui、codemode、mcp；agent-core 继续依赖 ai。此图不把 Durable 或 chord 放进 CLI 依赖链。',[
    n(40,244,'coding-agent','普通 CLI / SDK',w=240,h=120),
    n(600,20,'ai','模型接入',w=300),n(600,140,'agent-core','Agent 与循环',w=300),n(600,260,'tui','终端渲染',w=300),
    n(600,380,'codemode','独立沙箱库',w=300),n(600,500,'mcp','独立协议客户端',w=300)
],[('M280 260 H332 Q340 260 340 252 V72 Q340 64 348 64 H600',False),
   ('M280 280 H372 Q380 280 380 272 V192 Q380 184 388 184 H600',False),('M280 304 H600',False),
   ('M280 328 H452 Q460 328 460 336 V416 Q460 424 468 424 H600',False),
   ('M280 348 H412 Q420 348 420 356 V536 Q420 544 428 544 H600',False),('M850 140 V108',False)],height=652,
labels=[(40,620,'箭头表示直接内部依赖，省略第三方依赖；ai 还使用 telemetry。依据固定版本 package.json。')])

diagram('durable-package-dependencies','Durable 与远程执行的包关系','env 依赖 Durable 与 chord；Durable 依赖 ai、codemode、chord。这套独立运行时与普通 CLI 分开。',[
    n(360,28,'env','远程 ExecutionEnv / Rust daemon'),n(360,180,'durable','实验性持久任务 Harness'),
    n(40,340,'ai','模型调用'),n(360,340,'codemode','QuickJS 与确定性执行'),n(680,340,'chord','文档状态与 Context')
],[('M480 116 V180',False),
   ('M600 72 H928 Q936 72 936 80 V376 Q936 384 928 384 H920',False),
   ('M420 268 V284 Q420 292 412 292 H168 Q160 292 160 300 V340',False),('M480 268 V340',False),
   ('M540 268 V284 Q540 292 548 292 H792 Q800 292 800 300 V340',False)],height=508,
labels=[(40,478,'箭头表示直接内部依赖。普通 coding-agent 不依赖这套 Harness，也不会自动获得持久重放。')])

print(f'Generated {len(list(OUT.glob("*.svg")))} SVG diagrams.')
