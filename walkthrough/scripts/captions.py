#!/usr/bin/env python3
"""captions.py words_final.json states.json [fixes.json]   plain native-looking captions, 2-4 words at a time, timed to the final cut.
fixes.json = [["speed delete", "speed to lead"], ["being", "Bing"]]  (what whisper heard -> what he said; longest phrases first)."""
import json, sys, re, html
W = json.load(open(sys.argv[1])); fixes = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else []
key = lambda s: re.sub(r'[^a-z0-9\']', '', s.lower())
for frm, to in fixes:
    f = [key(x) for x in frm.split()]; i = 0
    while i <= len(W) - len(f):
        if [key(w['w']) for w in W[i:i + len(f)]] == f and len({w['seg'] for w in W[i:i + len(f)]}) == 1:
            tail = re.search(r'[.,!?]+$', W[i + len(f) - 1]['w']); W[i:i + len(f)] = [{'w': to + (tail.group(0) if tail else ''), 's': W[i]['s'], 'e': W[i + len(f) - 1]['e'], 'seg': W[i]['seg']}]
        i += 1
chunks = []; cur = []
def flush():
    global cur
    if cur: chunks.append(cur); cur = []
for i, w in enumerate(W):
    if cur and (w['seg'] != cur[-1]['seg'] or w['s'] - cur[-1]['e'] > 0.45 or len(' '.join(x['w'] for x in cur + [w])) > 24 or len(cur) >= 4): flush()
    cur.append(w)
    if re.search(r'[.!?]$', w['w']): flush()
flush()
for i in range(len(chunks) - 1, 0, -1):          # no orphan one-word lines: tuck a lone last word into the line before it
    a, b = chunks[i - 1], chunks[i]
    if len(b) == 1 and a[-1]['seg'] == b[0]['seg'] and b[0]['s'] - a[-1]['e'] < 0.45 and len(' '.join(x['w'] for x in a + b)) <= 32 and not re.search(r'[.!?]$', a[-1]['w']): chunks[i - 1] = a + b; del chunks[i]
states = []; cap = True
for i, c in enumerate(chunks):
    s = c[0]['s']; e = min(chunks[i + 1][0]['s'], c[-1]['e'] + 0.5) if i + 1 < len(chunks) else c[-1]['e'] + 0.4
    txt = ' '.join(x['w'] for x in c)
    if cap: txt = txt[0].upper() + txt[1:]
    cap = bool(re.search(r'[.!?]$', txt)); txt = re.sub(r'[.,]+$', '', txt)
    if e - s > 0.05: states.append({'s': round(s, 3), 'e': round(e, 3), 'html': html.escape(txt)})
json.dump(states, open(sys.argv[2], 'w'), indent=0); print(len(states), 'caption states'); print(' | '.join(s['html'] for s in states))
