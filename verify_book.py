"""本地出版物结构检查，不替代 EPUBCheck 或沙箱安全审计。"""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).parent
versions = json.loads((ROOT/'sources/versions.json').read_text())
VERSION = versions['target_version']

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images = [], [], []
        self.chapters = self.svg = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
            if tag == 'h1' and a['id'].startswith('chapter-'): self.chapters += 1
        if tag == 'a' and 'href' in a:self.links.append(a['href'])
        if tag == 'img':self.images.append(a.get('src',''))
        if tag == 'svg':self.svg += 1

page = Page()
page.feed((ROOT/'index.html').read_text())
assert not [k for k,v in Counter(page.ids).items() if v>1], 'duplicate IDs'
assert page.chapters == 12
assert page.svg == 12
for href in page.links:
    if href.startswith('#'):assert href[1:] in page.ids, href
    elif not re.match(r'https?://',href):assert (ROOT/href.split('#')[0]).is_file(), href
assert '{{' not in (ROOT/'index.html').read_text()

ns = {'s':'http://www.w3.org/2000/svg'}
for svg in (ROOT/'diagrams').glob('*.svg'):
    root = ET.parse(svg).getroot()
    assert root.get('role') == 'img'
    assert root[0].tag.endswith('title')
    assert root.find('s:desc',ns) is not None
    ids = {el.get('id') for el in root.iter() if el.get('id')}
    assert all(x in ids for x in root.get('aria-labelledby').split())

with zipfile.ZipFile(ROOT/'pi-architecture.zh-CN.epub') as z:
    assert z.namelist()[0] == 'mimetype'
    assert z.getinfo('mimetype').compress_type == zipfile.ZIP_STORED
    assert z.read('mimetype') == b'application/epub+zip'
    for name in z.namelist():
        if name.endswith(('.xml','.xhtml','.opf','.svg')):ET.fromstring(z.read(name))
    opf=ET.fromstring(z.read('OEBPS/content.opf'))
    pns={'p':'http://www.idpf.org/2007/opf'}
    items={i.get('id'):i for i in opf.findall('p:manifest/p:item',pns)}
    for item in items.values():assert 'OEBPS/'+item.get('href') in z.namelist()
    for item in opf.findall('p:spine/p:itemref',pns):assert item.get('idref') in items
    x=ET.fromstring(z.read('OEBPS/book.xhtml'))
    bookids={el.get('id') for el in x.iter() if el.get('id')}
    for el in x.iter():
        href=el.get('href','')
        if href.startswith('#'):assert href[1:] in bookids
        src=el.get('src','')
        if src:assert 'OEBPS/'+src in z.namelist()
    nav=ET.fromstring(z.read('OEBPS/nav.xhtml'))
    for el in nav.iter():
        href=el.get('href','')
        if href.startswith('book.xhtml#'):assert href.split('#')[1] in bookids

with zipfile.ZipFile(ROOT/f'pi-mono-v{VERSION}.zip') as z:
    data=json.loads(z.read(f'pi-v{VERSION}/packages/coding-agent/package.json'))
    assert data['version'] == VERSION
    assert len(z.namelist()) > 1000, 'empty or incomplete source archive'

html = (ROOT/'index.html').read_text()
assert f'本版核查版本 v{VERSION}' in html
assert f'book-v{VERSION}/pi-mono-v{VERSION}.zip' in html
for phrase in ('PI_CODEMODE_MAX_WORKERS', 'reserveTokens', 'images: [photo]', 's29'):
    assert phrase in html, f'missing v1.4.0 material: {phrase}'
source_md = (ROOT/'chapters/03-contracts-and-integration.md').read_text()
script = (ROOT/'examples/scripts/06-classify-image.js').read_text().split('\n', 1)[1].strip()
assert script in source_md, 'classifier code in the chapter differs from the runnable example'
with zipfile.ZipFile(ROOT/'pi-architecture.zh-CN.epub') as z:
    assert f'v{VERSION}' in z.read('OEBPS/content.opf').decode()
    assert 'PI_CODEMODE_MAX_WORKERS' in z.read('OEBPS/book.xhtml').decode()

subprocess.run(['node',str(ROOT/'examples/run-checks.mjs')],check=True)
assert (ROOT/'pi-architecture.zh-CN.pdf').read_bytes().startswith(b'%PDF-')
print('PASS: 12 chapters, 12 accessible SVGs, anchors, local links, EPUB XML/ZIP/manifest/navigation, source archive version, PDF header.')
print('Not performed here: upstream tests, real provider/MCP/cloud execution, sandbox security audit. EPUBCheck 5.2.1 is run separately.')
