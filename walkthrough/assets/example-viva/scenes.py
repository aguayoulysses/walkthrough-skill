#!/usr/bin/env python3
"""Viva El Volt walkthrough: what the screen half shows, timed to the words. Writes screen.json for rec.js."""
import json, os
W = os.path.dirname(os.path.abspath(__file__)); BD = os.path.join(W, '..', 'board')
tl = {s['id']: s for s in json.load(open(f'{W}/timeline.json'))['segments']}
words = json.load(open(f'{W}/words_final.json'))
OLD, NEW = 'https://vivaelvolt.com/', 'https://viva-el-volt-site.vercel.app/'
SITE = [1280, 884]

def T(seg, word=None, n=0, off=0.0):
    """absolute time of a segment start, or of the n-th word containing `word` inside it"""
    if word is None: return tl[seg]['t0'] + off
    ws = [w for w in words if w['seg'] == seg and word.lower() in w['w'].lower()]
    return ws[n]['s'] + off

scenes = []
def scene(id, a, b, acts=(), **k):
    t0, t1 = tl[a]['t0'] if isinstance(a, str) else a, tl[b]['t1'] if isinstance(b, str) else b
    out = []
    for x in acts:
        x = dict(x); x['t'] = round(x['t'] - t0, 3); assert -0.01 <= x['t'] < t1 - t0, (id, x); out.append(x)
    scenes.append(dict(id=id, t0=t0, t1=t1, actions=out, **k))

I = lambda item, box=None, **k: dict({'item': item}, **({'box': box} if box else {}), **k)
N = lambda item: {'item': item, 'part': '.txt'}                       # the text of a note / heading
def circle(t, on, dur=0.8, pad=8): return {'t': t, 'laser': 'circle', 'on': on, 'dur': dur, 'pad': pad}
def under(t, on, dur=0.6, times=1): return {'t': t, 'laser': 'underline', 'on': on, 'dur': dur, 'times': times, 'gap': 3}
def cam(t, c, dur=0.7): return {'t': t, 'cam': c, 'dur': dur}
def move(t, to, dur=None): return dict({'t': t, 'move': to}, **({'dur': dur} if dur else {}))
def board(id, a, b, at, frm, acts, **k): scene(id, a, b, acts, board=dict({'at': at}, **({'from': frm} if frm else {})), **k)

# ---------- website missing from the Google profile (board section 3)
s = 'S1'
board('gmb', s, s, 'f03-f', None, [
    cam(T(s, off=0.25), I('f03-i', pad=20)),
    circle(T(s, 'website', off=-0.25), I('f03-i', [.59, .60, .74, .72]), 0.8),
    under(T(s, 'Google', off=-0.1), I('f03-i', [.59, .685, .70, .705]), 0.5),
], mouse=[820, 640])

# ---------- his current site, live
A = []
A += [move(T('S2', off=0.3), [520, 420]), {'t': T('S2', 'linked', off=-0.2), 'scroll': 230, 'dur': 1.3}, cam(T('S2', 'linked'), {'w': 1040})]
# "This is AI generated" = the hero artwork (the mascot poster), not the headline
A += [cam(T('S3', off=-0.45), [560, 0, 720], 0.5), {'t': T('S3', off=-0.3), 'laser': 'circle', 'hover': True, 'on': {'sel': '#header', 'box': [.6, -.28, .95, .82]}, 'dur': 1.25, 'pad': 0, 'lead': 0.35}]
A += [{'t': T('S4', off=-0.15), 'scroll': {'sel': '#contact', 'top': 30}, 'dur': 1.0}, cam(T('S4', off=0.1), {'sel': '#contact', 'pad': 0}, 0.9),
      move(T('S4', 'form', off=-0.3), {'sel': '#form-contactSection input[name=name]'}), {'t': T('S4', 'actually'), 'click': True},
      {'t': T('S4', 'goes', off=-0.1), 'type': 'hello?', 'cps': 9}, move(T('S4', 'probably', off=0.1), {'text': 'MESSAGE US', 'within': '#contact'})]
A += [{'t': T('S5', off=-0.12), 'scroll': {'sel': '#features', 'top': 50}, 'dur': 0.9}, cam(T('S5', off=0.0), {'w': 1040}),
      move(T('S5', 'individual', off=-0.1), {'text': 'Read more', 'within': '#features', 'nth': 0})]
A += [move(T('S6', 'single', off=-0.2), {'text': 'Read more', 'within': '#features', 'nth': 1}, 0.4), move(T('S6', 'one', off=-0.1), {'text': 'Read more', 'within': '#features', 'nth': 2}, 0.4)]
A += [{'t': T('S7', off=-0.12), 'scroll': {'sel': '#testimonials', 'top': 30}, 'dur': 0.9}, cam(T('S7', off=0.0), {'w': 940}),
      move(T('S7', 'reviews', off=-0.3), {'sel': '#testimonials h1', 'at': [.4, .6]}), move(T('S7', 'fake', off=-0.5), [330, 500], 0.6),
      move(T('S7', 'should', off=0.0), [800, 560], 0.8), move(T('S7', 'Google', off=0.0), [560, 430], 0.6)]
A += [{'t': T('S8', off=-0.12), 'scroll': 99999, 'dur': 0.85}, cam(T('S8', off=0.8), {'sel': '#footer', 'pad': 150, 'min': 760}, 0.7),
      {'t': T('S8', 'NAP', off=-0.1), 'drag': {'from': {'sel': '#footer', 'at': [.38, .5]}, 'to': {'sel': '#footer', 'at': [.62, .5]}}, 'dur': 0.7}]
A += [cam(T('S9', off=-0.1), {'w': 1040}, 0.6), {'t': T('S9', off=-0.1), 'scroll': {'sel': '#links', 'top': 90}, 'dur': 0.7},
      move(T('S9', 'multiple', off=0.0), {'text': 'Follow us on Instagram'}, 0.45), move(T('S9', 'broken', off=0.0), {'text': 'Follow us on Facebook'}, 0.4),
      move(T('S9', 'links', off=0.05), {'text': 'Follow Us On LinkedIn'}, 0.4)]
scene('old', 'S2', 'S9', A, url=OLD, viewport=SITE, mouse=[760, 560], blockPost=True)

# ---------- "create them a fully new one": the real build file writing itself (face is the working b-roll)
scene('work', 'S10', 'S10', [], file=f'{W}/code.html', freeze='start', settle=300, cursor='none', viewport=SITE, cam=[0, 0, 720])

# ---------- the new site, live: entrance animation, real reviews, the form
A = [move(T('N1', 'animation', off=-0.6), {'sel': 'h1', 'at': [.55, .7]}), move(T('N1', 'enter', off=-0.1), {'text': 'Request a call back', 'within': '.hero'})]
A += [{'t': T('N2', off=-0.3), 'scroll': {'sel': '#reviews', 'top': 60}, 'dur': 0.9}, cam(T('N2', off=0.1), {'w': 1060}),
      move(T('N2', 'real', off=-0.1), {'sel': '.rv-c', 'nth': 0, 'at': [.5, .35]}), move(T('N2', 'embeds', off=-0.1), {'sel': '.rv-c', 'nth': 1, 'at': [.9, .12]}, 0.5),
      move(T('N2', 'look', off=-0.1), {'sel': '.rv-c', 'nth': 2, 'at': [.5, .4]}, 0.5)]
A += [{'t': T('N3', off=-0.25), 'scroll': {'sel': '#est', 'top': 190}, 'dur': 0.8}, cam(T('N3', off=0.3), {'sel': '#est', 'pad': 70}, 0.8),
      move(T('N3', 'form', off=0.0), {'sel': '#est .tf-step.on .tf-opt', 'nth': 0}), {'t': T('N3', 'actually', off=0.2), 'click': True},
      move(T('N3', 'after', off=-0.1), {'sel': '#est .tf-step.on .tf-opt', 'nth': 0}, 0.4), {'t': T('N3', 'fill', off=0.1), 'click': True},
      move(T('N3', 'out', off=0.15), {'sel': '#est .tf-step.on input'}, 0.35), {'t': T('N3', 'done', off=0.0), 'click': True},
      {'t': T('N3', 'done', off=0.15), 'type': 'Maria Lopez', 'cps': 16}]
txt = T('N3', 'client', off=-0.3)                                   # "the client will receive an automated text": cut to the texts themselves
scene('new', 'N1', txt, A, url=NEW, freeze='start', viewport=SITE, mouse=[930, 690], blockPost=True)

# the two texts the form sends. Wording = the real templates in happy-mouths/app/api/lead/[slug]/route.ts with this business filled in.
from urllib.parse import urlencode
t1 = T('N3', 'automated', off=0.0) - txt; t2 = T('N3b', 'notified', off=-0.5) - txt
Q = urlencode({'biz': 'Viva El Volt Electrical Services', 'cust': 'Maria Lopez', 'owner': 'Gonzalo', 't1': round(t1 * 1000), 't2': round(t2 * 1000),
               'a': 'Hi Maria, this is Viva El Volt Electrical Services. We got your request and will call or text you shortly. Reply STOP to opt out.',
               'b': 'New lead from your website: Maria Lopez \u00b7 A panel upgrade or breaker problem \u00b7 Upland. Their number: (909) 555-0142. "Panel keeps tripping when the AC kicks on" Open the Happy Mouths app to reply.'})
scene('texts', txt, 'N3b', [
    move(txt + t1 + 0.25, {'sel': '#b1', 'at': [.7, .6]}, 0.6), {'t': T('N3', 'confirming', off=0.1), 'drag': {'from': {'sel': '#b1', 'at': [.04, .22]}, 'to': {'sel': '#b1', 'at': [.75, .5]}}, 'dur': 0.9},
    cam(T('N3b', off=0.0), [642, 60, 580], 0.7), move(txt + t2 + 0.2, {'sel': '#b2', 'at': [.6, .5]}, 0.6),
], file=f'{W}/texts.html?' + Q, freeze='start', settle=600, viewport=SITE, mouse=[420, 620], cam=[58, 60, 580])

# "forms that just go to your email ... get lost": back to the form on his current site
scene('oldform', 'N4', 'N4', [
    move(T('N4', 'forms', off=-0.3), {'sel': '#form-contactSection input[name=name]'}, 0.6), move(T('N4', 'email', off=-0.3), {'sel': '#form-contactSection input[name=email]'}, 0.4),
    move(T('N4', 'lost', off=-0.2), {'text': 'MESSAGE US', 'within': '#contact'}, 0.6), move(T('N4', 'losing', off=-0.2), [930, 330], 0.7),
], url=OLD, viewport=SITE, scroll={'sel': '#contact', 'top': 30}, mouse=[820, 560], cam={'sel': '#contact', 'pad': 0}, blockPost=True)

# ---------- yesterday's audio over the new site (face is the working b-roll)
VS = f'{W}/vs.html'
scene('y1', 'Y1', 'Y1', [{'t': T('Y1', off=0.2), 'drag': {'from': {'sel': '#T-title', 'at': [0, .5]}, 'to': {'sel': '#T-title', 'at': [1, .5]}}, 'dur': 0.7}],
      file=VS, viewport=SITE, mouse=[420, 300], cam={'sel': '#T-title', 'pad': 50, 'min': 560})
scene('y2', 'Y2', 'Y2', [{'t': T('Y2', off=0.25), 'drag': {'from': {'sel': 'h1', 'at': [0, .22]}, 'to': {'sel': 'h1', 'at': [.17, .78]}}, 'dur': 0.9}],
      url=NEW, viewport=SITE, mouse=[640, 520], cam={'sel': 'h1', 'pad': 110, 'min': 700})
scene('y3', 'Y3', 'Y3', [{'t': T('Y3', off=0.15), 'drag': {'from': {'sel': 'p.nap', 'at': [0, .12]}, 'to': {'sel': 'p.nap', 'at': [.5, .9]}}, 'dur': 0.9}],
      url=NEW, viewport=SITE, scroll={'sel': 'p.nap', 'top': 430}, mouse=[620, 300], cam={'sel': 'p.nap', 'pad': 110, 'min': 700})
scene('y4', 'Y4', 'Y4', [move(T('Y4', off=0.1), {'sel': '.svc', 'nth': 0, 'at': [.5, .85]}, 0.4), move(T('Y4', 'page', off=-0.1), {'sel': '.svc', 'nth': 1, 'at': [.5, .85]}, 0.4),
                         move(T('Y4', 'service', off=-0.15), {'sel': '.svc', 'nth': 2, 'at': [.5, .85]}, 0.4)],
      url=NEW, viewport=SITE, scroll={'sel': '.svc-g', 'top': 150}, mouse=[300, 700], cam={'sel': '.svc-g', 'pad': 30})
scene('y5', 'Y5', 'Y5', [move(T('Y5', off=0.15), {'sel': 'iframe.map', 'at': [.5, .55]}, 0.6)],
      url=NEW, viewport=SITE, scroll={'sel': 'iframe.map', 'top': 200}, mouse=[500, 600], cam={'sel': 'iframe.map', 'pad': 70})
scene('y6', 'Y6', 'Y6', [{'t': T('Y6', 'real', off=-0.5), 'drag': {'from': {'sel': '#L-map td.n', 'at': [1, .12], 'dx': 12}, 'to': {'sel': '#L-map td.n', 'at': [1, .55], 'dx': 640}}, 'dur': 1.1}],
      file=VS, viewport=SITE, scroll={'sel': '#L-map', 'top': 330}, mouse=[520, 560], cam={'sel': '#L-map td.n', 'min': 760, 'dx': 330})
scene('y7', 'Y7', 'Y7', [{'t': T('Y7', off=0.25), 'scroll': {'sel': '#L-schema', 'top': -260}, 'dur': 1.5}, move(T('Y7', 'schema', off=-0.1), [300, 330], 0.5)],
      file=VS, viewport=SITE, scroll={'sel': '#L-schema', 'top': 160}, mouse=[520, 420], cam=[0, 70, 760])
split = T('Y8', 'robot', off=-0.2)
scene('y8a', 'Y8', split, [move(T('Y8', off=0.3), [330, 190], 0.6)], url=NEW + 'sitemap.xml', viewport=SITE, mouse=[520, 420], cam=[0, 0, 820])
scene('y8b', split, 'Y9', [move(split + 0.2, [150, 40], 0.5), {'t': T('Y9', 'AI', off=-0.9), 'drag': {'from': [8, 68], 'to': [150, 190]}, 'dur': 1.0}],
      url=NEW + 'robots.txt', viewport=SITE, mouse=[420, 330], cam=[0, 0, 640])

# ---------- the audit board, section by section, with its own laser
s = 'B5'
board('b5', 'B5', 'B5c', 'f05-f', None, [
    under(T('B5', 'top', off=-0.2), N('f05-h'), 0.7), cam(T('B5b', off=-0.45), I('f05-i', pad=25)),
    circle(T('B5b', 'second', off=-0.2), I('f05-i', [.17, .385, .48, .55]), 0.85), under(T('B5b', '17', off=-0.05), I('f05-i', [.17, .41, .31, .44]), 0.4),
    {'t': T('B5c', 'opportunity', off=-0.2), 'laser': 'line', 'from': I('f05-i', at=[.12, .47]), 'to': I('f05-i', at=[.12, .2]), 'dur': 0.6},
    circle(T('B5c', 'competitiveness', off=0.0), I('f05-i', [.17, .2, .34, .245]), 0.7),
], mouse=[1050, 420], cam={'w': 1150})
board('b6', 'B6', 'B6', 'f06-f', 'f05-f', [
    cam(T('B6', off=0.7), I('f06-i', pad=25), 0.6), circle(T('B6', '14', off=-0.2), I('f06-i', [.045, .285, .16, .33]), 0.7, 10),
    cam(T('B6', 'activation', off=-0.7), 'full', 0.5), {'t': T('B6', 'activation', off=-0.55), 'key': 'ArrowRight'},
    cam(T('B6', 'make', off=-0.1), {'w': 1000}), under(T('B6', 'make', off=0.0), N('rv1-h'), 0.8), circle(T('B6', 'past', off=-0.3), N('rv1-a'), 0.9, 4),
], mouse=[700, 500])
board('b7', 'B7', 'B7', 'rv1-f', None, [
    circle(T('B7', 'write', off=-0.25), I('rv1-i', [.2, .4, .68, .63]), 0.85), circle(T('B7', 'send', off=-0.15), I('rv1-i2', [.22, .6, .98, .82]), 0.85),
    under(T('B7', 'actually', off=-0.1), N('rv1-a'), 0.7),
], mouse=[620, 560], cam={'w': 960})
board('b8', 'B8', 'B8', 'rv3-f', 'rv1-f', [
    cam(T('B8', off=0.7), {'w': 1000}), circle(T('B8', 'works', off=0.25), I('rv3-i1', [.4, .58, .6, .98]), 0.6), circle(T('B8', 'correctly', off=-0.1), I('rv3-i2', [.4, .58, .6, .98]), 0.6),
    under(T('B8', 'big', off=0.0), N('rv3-a'), 0.6),
], mouse=[700, 500])
board('b9', 'B9', 'B9e', 'f09-f', 'rv3-f', [
    cam(T('B9', off=0.7), {'w': 1000}), under(T('B9', off=0.8), N('f09-h'), 0.6), cam(T('B9b', 'wrong', off=-0.4), I('f09-i', pad=25)),
    circle(T('B9b', 'wrong', off=-0.15), I('f09-i', [.02, .225, .2, .285]), 0.75), cam(T('B9c', off=0.0), {'w': 880}), under(T('B9c', off=0.25), N('f09-a'), 0.8),
    under(T('B9d', off=0.2), N('f09-b'), 0.7), circle(T('B9e', 'pulls', off=-0.2), N('f09-b'), 0.9, 6),
], mouse=[700, 500])
board('b10', 'B10', 'B10', 'f10-f', 'f09-f', [
    cam(T('B10', off=0.7), {'w': 1000}), under(T('B10', off=0.8), N('f10-h'), 0.6), cam(T('B10', 'Google', off=-0.6), I('f10-i', pad=25)),
    circle(T('B10', 'Google', off=-0.1), I('f10-i', [.05, .47, .83, .555]), 0.7), circle(T('B10', 'Yelp', off=-0.1), I('f10-i', [.05, .57, .83, .655]), 0.6),
    circle(T('B10', 'Nextdoor', off=-0.1), I('f10-i', [.05, .67, .83, .755]), 0.6),
], mouse=[700, 500])
board('b11', 'B11', 'B11', 'f11-f', 'f10-f', [
    cam(T('B11', off=0.7), I('f11-i', pad=25)), circle(T('B11', off=0.85), I('f11-i', [.15, .115, .42, .175]), 0.6),
    {'t': T('B11', 'claim', off=-0.5), 'laser': 'line', 'from': I('f11-i', at=[.2, .25]), 'to': I('f11-i', at=[.2, .9]), 'dur': 0.8},
], mouse=[700, 500])
board('b12', 'B12', 'B12c', 'f12-f', 'f11-f', [
    cam(T('B12', off=0.7), I('f12-i', pad=20)), circle(T('B12', off=0.95), I('f12-i', [.05, .2, .88, .5]), 0.9, 2),
    circle(T('B12b', off=0.15), I('f12-i', [.05, .57, .88, .96]), 1.0, 2), under(T('B12c', 'see', off=-0.1), I('f12-i', [.05, .6, .86, .65]), 0.5),
], mouse=[700, 500])
board('b13', 'B13', 'B13d', 'f13-f', 'f12-f', [
    cam(T('B13', off=0.7), I('f13-i', pad=20)), circle(T('B13a', 'two', off=-0.25), I('f13-i', [.05, .3, .38, .385]), 0.7),
    circle(T('B13b', 'EV', off=-0.1), I('f13-i', [.055, .685, .265, .755]), 0.5, 4), circle(T('B13b', 'panel', off=-0.1), I('f13-i', [.27, .685, .415, .755]), 0.45, 4),
    circle(T('B13b', 'lighting', off=-0.1), I('f13-i', [.42, .685, .515, .755]), 0.4, 4), circle(T('B13c', 'generators', off=-0.1), I('f13-i', [.52, .685, .735, .755]), 0.5, 4),
    circle(T('B13c', 'security', off=-0.1), I('f13-i', [.055, .76, .33, .83]), 0.5, 4),
    cam(T('B13d', off=0.2), {'w': 880}), under(T('B13d', off=0.35), N('f13-b'), 0.8), circle(T('B13d', 'missing', off=-0.2), N('f13-b'), 0.9, 6),
], mouse=[700, 500])
board('b14', 'B14', 'B14', 'f14-f', 'f13-f', [
    cam(T('B14', off=0.7), I('f14-i', pad=25)), circle(T('B14', off=0.85), I('f14-i', [.03, .2, .27, .43]), 0.8),
    cam(T('B14', 'fill', off=-0.4), {'w': 880}), under(T('B14', 'fill', off=-0.15), N('f14-c'), 0.7),
], mouse=[700, 500])
board('b15', 'B15', 'B15', 'f15-f', 'f14-f', [
    cam(T('B15', off=0.7), I('f15-i', pad=25)), circle(T('B15', 'only', off=-0.1), I('f15-i', [.29, .27, .7, .52]), 0.8),
    circle(T('B15', 'without', off=-0.1), I('f15-i', [.29, .78, .7, .88]), 0.6), cam(T('B15', 'make', off=-0.2), {'w': 880}), under(T('B15', 'reply', n=1, off=-0.2), N('f15-c'), 0.6),
], mouse=[700, 500])
board('b16', 'B16', 'B16e', 'f16-f', 'f15-f', [
    cam(T('B16', off=0.7), I('f16-i', pad=25)), circle(T('B16', 'trust', off=-0.1), I('f16-i', [.04, .57, .9, .92]), 1.0, 2),
    circle(T('B16b', off=0.05), I('f16-i', [.345, .725, .555, .795]), 0.5, 4), circle(T('B16c', off=0.05), I('f16-i', [.06, .795, .235, .865]), 0.5, 4),
    circle(T('B16d', off=0.05), I('f16-i', [.06, .655, .325, .725]), 0.5, 4), circle(T('B16d', 'Chamber', n=1, off=-0.7), I('f16-i', [.33, .655, .585, .725]), 0.5, 4),
    cam(T('B16e', off=0.0), {'w': 880}), under(T('B16e', off=0.15), N('f16-b'), 0.8),
], mouse=[700, 500])
board('b17', 'B17', 'B17c', 'f17-f', 'f16-f', [
    cam(T('B17', off=0.7), I('f17-i', pad=25)), under(T('B17', 'consistency', off=-0.1), I('f17-i', [.03, .45, .36, .53]), 0.45),
    under(T('B17', 'business', off=-0.2), I('f17-i', [.03, .55, .33, .63]), 0.4), under(T('B17', 'fix', off=-0.3), I('f17-i', [.03, .65, .27, .73]), 0.4),
    circle(T('B17b', off=-0.1), I('f17-i', [.03, .745, .37, .845]), 0.7, 5), under(T('B17c', off=0.1), I('f17-i', [.03, .76, .36, .83]), 0.45, 2),
], mouse=[700, 500])
board('cta', 'CTA', 'CTA', 'f17-f', None, [
    under(T('CTA', off=0.2), N('f17-f'), 0.7), circle(T('CTA', 'audit', off=-0.1), N('f17-f'), 1.0, 10),
], mouse=[700, 500])

for a, b in zip(scenes, scenes[1:]): assert abs(a['t1'] - b['t0']) < 1e-6, ('gap', a['id'], b['id'])
json.dump({'viewport': [1440, 995], 'panel': [1080, 746], 'out': f'{W}/screen',
           'board': {'html': f'{BD}/board.html', 'items': f'{BD}/items', 'blobs': f'{BD}/blob', 'title': 'Viva El Volt Audit'}, 'scenes': scenes}, open(f'{W}/screen.json', 'w'), indent=1)
print(len(scenes), 'scenes', scenes[0]['t0'], '->', scenes[-1]['t1'])
