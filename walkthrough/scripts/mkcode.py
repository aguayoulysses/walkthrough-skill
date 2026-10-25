#!/usr/bin/env python3
"""mkcode.py <source file> <out.html> [tab name]   a dark code editor where the REAL file writes itself in, for the "building it" b-roll beat.
Record it with "file": out.html, "freeze": "start", "cursor": "none". ?lps=70 = lines per second."""
import sys, html, os, re
src = open(sys.argv[1]).read().split('\n')[:900]; tab = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(sys.argv[1])
TOK = re.compile(r"""(//.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`[^`]*`)|\b(const|let|var|function|return|import|from|export|if|else|for|of|await|async|class|new)\b""")
def color(l):
    out, i = '', 0
    for m in TOK.finditer(l):
        out += html.escape(l[i:m.start()]); cls = 'c' if m.group(1) else 's' if m.group(2) else 'k'
        out += f'<i class="{cls}">{html.escape(m.group(0))}</i>'; i = m.end()
    return out + html.escape(l[i:])
lines = ''.join(f'<div class="l"><b>{i}</b><span>{color(l) or " "}</span></div>' for i, l in enumerate(src, 1))
open(sys.argv[2], 'w').write('''<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;height:100%;background:#1e1e1e;color:#d4d4d4;font:15px/1.5 Menlo,Monaco,monospace;overflow:hidden}
#bar{height:38px;background:#252526;display:flex;align-items:end;padding-left:12px;font:13px -apple-system,sans-serif}
#bar div{background:#1e1e1e;color:#fff;padding:9px 18px;border-top:1px solid #0a84ff}#bar div+div{background:#2d2d2d;color:#969696;border-top-color:transparent}
#code{height:calc(100% - 38px);overflow:hidden}.l{display:none;white-space:pre}.l.on{display:flex}.l b{width:58px;text-align:right;padding-right:18px;color:#6e7681;font-weight:400;flex:none}
.k{color:#569cd6;font-style:normal}.s{color:#ce9178;font-style:normal}.c{color:#6a9955;font-style:normal}
#caret{display:inline-block;width:9px;height:19px;background:#aeafad;vertical-align:-3px}
</style><div id="bar"><div>''' + html.escape(tab) + '''</div><div>theme.css</div><div>site.js</div></div><div id="code">''' + lines + '''</div><script>
const L=[...document.querySelectorAll('.l')],code=document.getElementById('code'),lps=+new URLSearchParams(location.search).get('lps')||70;let n=0;
const c=document.createElement('span');c.id='caret';
setInterval(()=>{for(let k=0;k<Math.max(1,Math.round(lps/30));k++){if(n>=L.length)return;L[n].classList.add('on');L[n].lastChild.appendChild(c);n++}code.scrollTop=code.scrollHeight},1000/30);
</script>''')
print('wrote', sys.argv[2])
