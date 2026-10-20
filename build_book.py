"""从中文章节生成 HTML、EPUB 与 Markdown；PDF 用浏览器另行导出。"""
from pathlib import Path
import datetime
import html
import json
import re
import subprocess
import uuid
import zipfile
import xml.etree.ElementTree as ET
from markdown_it import MarkdownIt

ROOT = Path(__file__).parent
TITLE = '从工具循环到 Code Mode'
SUBTITLE = 'Pi 架构演进：v0.9.4、v0.99.2 与 v1.3.0'
CSS = '''
:root{--paper:#f5f4ed;--panel:#faf9f5;--ink:#20201d;--muted:#6b6a64;--line:#dedbd0;--brand:#1B365D}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.95 "Noto Serif CJK SC",Charter,Georgia,serif;font-variant-numeric:tabular-nums}
a{color:var(--brand);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}
.layout{max-width:1320px;margin:auto;display:grid;grid-template-columns:260px minmax(0,1fr);gap:50px;padding:38px 36px 100px}
nav.toc{position:sticky;top:28px;align-self:start;max-height:92vh;overflow:auto;font:14px/1.8 "Noto Sans CJK SC",sans-serif}
nav.toc>a{display:block;padding:5px 0;text-decoration:none}nav.toc .nav-title{font-size:18px;margin-bottom:14px}
main{min-width:0;max-width:900px}.edition{font:14px/1.8 "Noto Sans CJK SC",sans-serif;color:var(--muted);letter-spacing:.02em;margin-bottom:30px}
h1,h2,h3,h4,strong,b{font-weight:500}h1{font-size:31px;line-height:1.5;letter-spacing:-.02em;margin:90px 0 28px;scroll-margin-top:30px}
h1#cover{font-size:52px;line-height:1.35;margin:30px 0 22px;max-width:730px}h2{font-size:24px;line-height:1.55;border-left:3px solid var(--brand);padding-left:13px;margin:28px 0 25px}
h3{font-size:21px;line-height:1.65;margin:36px 0 12px}p{margin:16px 0}li{margin:7px 0}ul{list-style-type:disc}ol{list-style-type:decimal}ul,ol{padding-left:1.6em}
code,pre{font-family:"Noto Sans Mono",Consolas,monospace}code{font-size:.87em;background:#eae7dd;padding:2px 5px;border-radius:3px;overflow-wrap:anywhere}
pre{background:#eeece3;border:1px dotted var(--line);padding:20px 22px;line-height:1.75;overflow:auto;font-size:13px;margin:24px 0;border-radius:4px}
pre code{padding:0;background:none;font-size:inherit;white-space:pre;overflow-wrap:normal}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.9;margin:26px 0;table-layout:auto}th{text-align:left;font-weight:500;background:#eeece3}
th,td{padding:12px 11px;border-bottom:1px dotted #c6c1b2;vertical-align:top;overflow-wrap:anywhere}td:first-child{min-width:95px}
figure{margin:32px 0;padding:18px 0;border-top:1px dotted var(--line);border-bottom:1px dotted var(--line);break-inside:avoid}
figure svg,figure img{display:block;max-width:100%;height:auto;width:100%}figcaption{font:14px/1.8 "Noto Sans CJK SC",sans-serif;color:var(--muted);margin-top:14px}
blockquote{margin:24px 0;border-left:3px solid var(--brand);padding:1px 20px;color:var(--muted)}em,i,cite{font-style:normal}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0 40px}.tools a,button{display:inline-block;border:1px solid #bcb7a7;border-radius:4px;background:var(--panel);padding:8px 14px;color:var(--brand);font:14px/1.7 "Noto Sans CJK SC",sans-serif;text-decoration:none;cursor:pointer}
:focus-visible{outline:3px solid var(--brand);outline-offset:4px}.source{margin:24px 0;padding-bottom:20px;border-bottom:1px dotted var(--line);font-size:15px}.source p{margin:6px 0}.source .path{font:12px/1.8 monospace;color:var(--muted);overflow-wrap:anywhere}
.playground{padding:24px;border:1px dotted #bcb7a7;margin:34px 0;background:var(--panel)}.playground h3{margin-top:0}.playground label{display:block;font-size:15px;margin:14px 0}.playground input{display:block;width:100%;accent-color:var(--brand);margin-top:8px}.readout{font-size:21px;color:var(--brand)}.small{font-size:14px;color:var(--muted)}
.print-toc{display:none}footer{margin-top:60px;padding-top:24px;border-top:1px dotted var(--line);font-size:14px;color:var(--muted)}
@media(max-width:1000px){.layout{display:block;padding:24px 24px 70px}nav.toc{position:static;max-height:none;padding-bottom:25px;border-bottom:1px dotted var(--line);margin-bottom:36px;columns:2}nav.toc .nav-title{column-span:all}main{margin:auto}h1#cover{font-size:42px}}
@media(max-width:700px){figure{overflow-x:auto;padding-bottom:6px}figure svg{min-width:680px}figure figcaption{min-width:0}}
@media(max-width:600px){body{font-size:16px}.layout{padding:20px 16px 60px}nav.toc{columns:1}h1#cover{font-size:35px}h1{font-size:26px}h2{font-size:21px}table{font-size:12px}th,td{padding:9px 6px}td:first-child{min-width:0}pre{font-size:11px;padding:13px}figure{margin:25px 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@page{size:A4;margin:18mm 16mm 20mm;@bottom-right{content:counter(page);font:9pt sans-serif;color:#6b6a64}}
@media print{.print-toc{display:block;break-before:page}.print-toc a{display:block;font-size:11pt;margin:8px 0}.print-toc h2{margin-top:15mm}html{scroll-behavior:auto}body{background:#fff;font-size:10.5pt;line-height:1.85}.layout{display:block;padding:0;max-width:none}main{max-width:none}nav.toc,.tools,.playground input,.playground label,button,.screen-only{display:none!important}h1{break-before:page;font-size:24pt;margin:15mm 0 8mm}h1#cover{break-before:auto;font-size:37pt;margin-top:25mm}h2{font-size:18pt}h3{font-size:14pt;break-after:avoid}p,li{orphans:3;widows:3}table{font-size:8.5pt}thead{display:table-header-group}tr{break-inside:avoid}pre{white-space:pre-wrap;font-size:8pt;overflow:visible;break-inside:avoid}pre code{white-space:pre-wrap;overflow-wrap:anywhere}figure{padding:10px 0;break-inside:avoid}figcaption{font-size:9pt}.source{break-inside:avoid}a{color:inherit;text-decoration:none}.edition{font-size:10pt}footer{break-before:page}}
'''
DEMO = '''<aside class="playground" aria-labelledby="demo-title">
<h3 id="demo-title">动手调一调：多少信息需要跨回模型？</h3>
<p>修改调用数量与结果大小，观察字段筛选前后的字符量。这里只算数据字符，不估算 token、费用或实际耗时。</p>
<label for="call-count">独立调用数量：<output id="count-label">12</output><input id="call-count" type="range" min="1" max="60" value="12" /></label>
<label for="raw-size">每项原始结果字符：<output id="raw-label">20,000</output><input id="raw-size" type="range" min="1000" max="50000" step="1000" value="20000" /></label>
<p class="readout" id="demo-result" aria-live="polite">240,000 字符 → 3,600 字符</p>
<p class="small">假设每项只返回 300 字符，忽略脚本与外层包装。工具本身可能已有截断；这不是实测速度对比。</p>
</aside>'''
JS = '''
const count = document.getElementById('call-count');
const raw = document.getElementById('raw-size');
function updateDemo(){
 const n=Number(count.value), r=Number(raw.value), f=x=>x.toLocaleString('zh-CN');
 document.getElementById('count-label').textContent=f(n);
 document.getElementById('raw-label').textContent=f(r);
 document.getElementById('demo-result').textContent=f(n*r)+' 字符 → '+f(n*300)+' 字符';
}
count.addEventListener('input',updateDemo);raw.addEventListener('input',updateDemo);
document.getElementById('print-book').addEventListener('click',()=>window.print());
updateDemo();
'''

sources = json.loads((ROOT/'sources/source-index.json').read_text())
versions = json.loads((ROOT/'sources/versions.json').read_text())
source_md = '\n# 来源索引与核查范围\n\n所有文件链接固定到对应版本标签。方括号来源编号可从正文跳转；源码副本位于同目录 `sources/`。\n\n'
for source in sources:
    if source.get('kind') == 'release':
        url = 'https://github.com/earendil-works/pi/releases/tag/v1.3.0'
    elif source.get('kind') == 'commit':
        sha = subprocess.check_output(['git','-C',str(ROOT/'sources/pi-mono'),'rev-parse',source['commit']],text=True).strip()
        url = f'https://github.com/earendil-works/pi/commit/{sha}'
    else:
        tag = source.get('tag','v1.3.0')
        local = ROOT/'sources'/({'v0.9.4':'pi-v0.9.4','v0.99.2':'pi-v0.99.2'}.get(tag,'pi-mono'))/source['path']
        assert local.is_file(), local
        url = f'https://github.com/earendil-works/pi/blob/{tag}/{source["path"]}'
    source['url'] = url
    source_md += f'<div class="source" id="{source["id"]}">\n\n**[{source["id"].upper()}] [{source["title"]}]({url})**\n\n{source["note"]}\n\n</div>\n\n'
source_md += '''## 核查范围与限制

本书对照官方发布 API、三个固定标签、相关包清单、主运行链文档、核心循环及 Code Mode 适配实现，保存了完整 diff 清单。书中代码区分可运行示例与占位伪代码。

教学脚本使用 Node 和模拟工具验证。HTML、PDF、EPUB 另做渲染或结构检查。没有运行完整上游测试套件，没有部署 Cloudflare 或 SSH 环境，没有用付费模型验证生成质量，没有做沙箱安全审计；上游测量数据明确标注为上游结果。

优先深入阅读：S7 建立全景；S10 理解脚本契约；S13 研究独立沙箱和部署；S15 理解嵌套工具与扩展；S23 理解实验性持久执行。

## 固定提交

'''
for tag, sha in versions['versions'].items():
    source_md += f'- `{tag}`：`{sha}`\n'
source_md += '\n来源材料为官方仓库中的文档与源码；电子书是整理后的教学解释，不代表项目官方文档。\n'
book = '\n\n'.join(p.read_text() for p in sorted((ROOT/'chapters').glob('*.md'))) + '\n\n' + source_md
(ROOT/'book.zh-CN.md').write_text(book)
md = MarkdownIt('commonmark', {'html':True,'xhtmlOut':True}).enable('table')
tokens = md.parse(book)
toc = []
for i, token in enumerate(tokens):
    if token.type == 'heading_open' and token.tag == 'h1':
        title = tokens[i+1].content
        match = re.match(r'第 (\d+) 章',title)
        anchor = f'chapter-{match[1]}' if match else ('cover' if not toc else 'sources')
        token.attrSet('id',anchor)
        toc.append((anchor,title))
content = md.renderer.render(tokens,md.options,{})
# Markdown 的独立图片转换成语义化 figure，HTML 内嵌 SVG，EPUB 保留图片资源。
def figures(text, inline):
    def replace(match):
        src, alt = match.groups()
        picture = (ROOT/src).read_text() if inline else f'<img src="{src}" alt="{alt}" />'
        return f'<figure>{picture}<figcaption>{alt}</figcaption></figure>'
    return re.sub(r'<p><img src="(diagrams/[^\"]+)" alt="([^\"]*)"\s*/></p>',replace,text)

nav = ''.join(f'<a href="#{anchor}">{html.escape(title)}</a>' for anchor,title in toc)
body = figures(content,True)
body = body.replace('<h1 id="chapter-6">',DEMO+'<h1 id="chapter-6">')
printed_toc = '<section class="print-toc" aria-label="打印版目录"><h2>目录</h2>' + ''.join(f'<a href="#{a}">{html.escape(t)}</a>' for a,t in toc if a != 'cover') + '</section>'
body = body.replace('<h1 id="chapter-1">',printed_toc+'<h1 id="chapter-1">')
scaffold = ROOT/'research-scaffold.html'
if not scaffold.exists():
    scaffold.write_text((ROOT/'index.html').read_text())
head = scaffold.read_text().split('</head>')[0].replace('<html lang="en">','<html lang="zh-CN">')
head = re.sub(r'<title>.*?</title>',f'<title>{TITLE} · Pi 中文架构电子书</title>',head)
# 保留初始化器的主题 token；阅读与打印布局不依赖 CDN 成功加载。
head += f'<style>{CSS}</style></head>'
result = head + f'''<body><div class="layout"><nav class="toc" aria-label="章节目录"><div class="nav-title">Pi 架构演进</div>{nav}</nav>
<main><header class="edition">中文源码导读 · 2026-10-20 · 最新核查版本 v1.3.0<br />12 章 · {len(list((ROOT/'diagrams').glob('*.svg')))} 张架构图 · 5 个可验证脚本</header>
<div class="tools"><a href="pi-architecture.zh-CN.pdf">下载 PDF</a><a href="pi-architecture.zh-CN.epub">下载 EPUB</a><a href="book.zh-CN.md">Markdown 原稿</a><a href="https://github.com/StarDust0083-GP03/pi-mono-architecture-book/releases/download/book-v1.3.0/pi-mono-v1.3.0.zip">v1.3.0 源码 ZIP</a><button id="print-book" type="button">打印 / 存为 PDF</button></div>
{body}<footer>阅读建议：先运行教学检查，再对照固定版本源码核对你需要迁移的接口。下载的是源码，没有修改当前 Pi 安装。</footer></main></div><script>{JS}</script></body></html>'''
(ROOT/'index.html').write_text(result)

# EPUB 3：静态内容，完整中文目录与 SVG 资源，无外部脚本、字体或样式依赖。
epub_body = figures(content,False)
# 确认 Markdown 渲染出的片段是有效 XHTML。
ET.fromstring('<div>'+epub_body+'</div>')
identifier = str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/earendil-works/pi/v1.3.0/zh-ebook'))
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
navitems = ''.join(f'<li><a href="book.xhtml#{a}">{html.escape(t)}</a></li>' for a,t in toc)
epub_css = re.sub(r'@page\{.*?\}\}', '', CSS, flags=re.S) + '\nbody{padding:1em}h1#cover{font-size:2.3em}h1{break-before:page}table{font-size:.8em}pre,pre code{white-space:pre-wrap;overflow-wrap:anywhere}figure img{max-width:100%;height:auto}h2{font-size:1.3em}'
xhtml = f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN"><head><title>{TITLE}</title><link rel="stylesheet" type="text/css" href="style.css" /></head><body>{epub_body}</body></html>'
navdoc = f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN"><head><title>目录</title></head><body><nav epub:type="toc" id="toc"><h1>目录</h1><ol>{navitems}</ol></nav></body></html>'
svg_files = sorted((ROOT/'diagrams').glob('*.svg'))
manifest = ''.join(f'<item id="svg{i}" href="diagrams/{p.name}" media-type="image/svg+xml" />' for i,p in enumerate(svg_files))
opf = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:uuid:{identifier}</dc:identifier><dc:title>{TITLE}：{SUBTITLE}</dc:title><dc:language>zh-CN</dc:language><dc:creator>AI 辅助源码研究</dc:creator><meta property="dcterms:modified">{now}</meta></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" /><item id="book" href="book.xhtml" media-type="application/xhtml+xml" /><item id="css" href="style.css" media-type="text/css" />{manifest}</manifest><spine><itemref idref="book" /></spine></package>'''
container = '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" /></rootfiles></container>'
with zipfile.ZipFile(ROOT/'pi-architecture.zh-CN.epub','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
    for name,value in [('META-INF/container.xml',container),('OEBPS/content.opf',opf),('OEBPS/book.xhtml',xhtml),('OEBPS/nav.xhtml',navdoc),('OEBPS/style.css',epub_css)]:
        z.writestr(name,value)
    for p in svg_files:z.write(p,'OEBPS/diagrams/'+p.name)
print(f'Built HTML, EPUB, Markdown; {len(toc)-2} chapters, {len(svg_files)} diagrams, {len(sources)} source entries.')
