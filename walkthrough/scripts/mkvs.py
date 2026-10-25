#!/usr/bin/env python3
"""mkvs.py <url> <out.html>   a Chrome "view-source:" look-alike of the page's REAL html, for the title tag / schema / embed beats.
Lines that matter get ids to aim at: #L-title, #L-desc, #L-h1, #L-map (first iframe), #L-schema (JSON-LD), plus #T-<id> = just the text inside."""
import sys, re, html, urllib.request
src = urllib.request.urlopen(urllib.request.Request(sys.argv[1], headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf8', 'replace')
src = re.sub(r'>\s*<', '>\n<', src)                       # one tag per line so the line we point at is short
src = re.sub(r'(<script type="application/ld\+json">)', r'\1\n', src)
def pretty_ld(m):
    import json
    try: return json.dumps(json.loads(m.group(1)), indent=2, ensure_ascii=False) + '\n'
    except Exception: return m.group(1)
src = re.sub(r'(?<=<script type="application/ld\+json">\n)(.*?)(?=</script>)', pretty_ld, src, flags=re.S)
def color(line):
    out = html.escape(line)
    out = re.sub(r'(&lt;/?)([\w:-]+)', r'\1<span class="t">\2</span>', out)
    out = re.sub(r'([\w:-]+)=(&quot;.*?&quot;)', r'<span class="a">\1</span>=<span class="v">\2</span>', out)
    return out
rows = []; seen = set()
for i, line in enumerate(src.split('\n'), 1):
    lid = ''
    for key, pat in (('title', '<title>'), ('desc', 'name="description"'), ('h1', '<h1'), ('map', '<iframe'), ('schema', 'application/ld+json')):
        if pat in line and key not in seen: seen.add(key); lid = key
    body = color(line)
    if lid in ('title', 'h1'): body = re.sub(r'(&gt;)([^<&][^<]*?)(&lt;/)', lambda m: f'{m.group(1)}<span id="T-{lid}">{m.group(2)}</span>{m.group(3)}', body, count=1)
    rows.append(f'<tr{" id=L-" + lid if lid else ""}><td class="n">{i}</td><td class="c">{body}</td></tr>')
open(sys.argv[2], 'w').write('''<!doctype html><meta charset="utf-8"><title>view-source</title><style>
body{margin:0;background:#fff;font:13px/1.45 Menlo,Monaco,monospace;color:#000}table{border-collapse:collapse;width:100%}
td.n{width:52px;text-align:right;padding:0 10px 0 4px;color:#80868b;border-right:1px solid #dadce0;vertical-align:top;user-select:none;background:#f8f9fa}
td.c{padding:0 8px;white-space:pre-wrap;word-break:break-all}.t{color:#881280}.a{color:#994500}.v{color:#1a1aa6}::selection{background:#b3d4fc}
</style><table>''' + '\n'.join(rows) + '</table>')
print('wrote', sys.argv[2], len(rows), 'lines; ids:', sorted(seen))
