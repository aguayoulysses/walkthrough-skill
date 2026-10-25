#!/usr/bin/env node
// rec.js spec.json [sceneId ...]   -> <out>/<sceneId>/f00000.jpg ...
// Fake screen recording. Loads a real page (or the audit board) in headless Chrome at a desktop viewport and
// plays a scripted, human-looking mouse over it, one video frame at a time. The page clock is frozen and stepped
// 1/fps per frame, so page animations, hover states and the board's own laser render exactly, however slow the capture.
// A virtual camera (screenshot clip) zooms and follows the cursor so the text is readable in the small panel.
// Spec format and every action are documented in ../SKILL.md.
const puppeteer = require('puppeteer-core'); const fs = require('fs'); const path = require('path');
const spec = JSON.parse(fs.readFileSync(process.argv[2])); const only = process.argv.slice(3);
const [PW, PH] = spec.panel || [1080, 746];
const FPS = spec.fps || 30000 / 1001; const OUT = path.resolve(spec.out || 'screen'); const AR = PH / PW;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const mj = (u) => u * u * u * (10 - 15 * u + 6 * u * u); // minimum-jerk: how a hand actually accelerates
let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

// Runs in the page before any of its scripts: a clock we can freeze and step.
const CLOCK = `(() => { if (window.__clk) return;
  const P = performance, RN = P.now.bind(P), DN = Date.now.bind(Date), RAF = requestAnimationFrame.bind(window), CAF = cancelAnimationFrame.bind(window),
    ST = setTimeout.bind(window), CT = clearTimeout.bind(window), SI = setInterval.bind(window), CI = clearInterval.bind(window);
  let fz = false, vt = 0, d0 = 0, id = 1e9; const raf = new Map(), tm = new Map(), seen = new WeakMap();
  P.now = () => (fz ? vt : RN()); Date.now = () => (fz ? Math.round(d0 + vt) : DN());
  window.requestAnimationFrame = (cb) => { if (!fz) return RAF(cb); raf.set(++id, cb); return id; };
  window.cancelAnimationFrame = (i) => { raf.delete(i); CAF(i); };
  window.setTimeout = (cb, ms, ...a) => { if (!fz) return ST(cb, ms, ...a); tm.set(++id, { cb, at: vt + (+ms || 0), a }); return id; };
  window.setInterval = (cb, ms, ...a) => { if (!fz) return SI(cb, ms, ...a); tm.set(++id, { cb, at: vt + (+ms || 0), a, every: Math.max(+ms || 0, 4) }); return id; };
  window.clearTimeout = (i) => { tm.delete(i); CT(i); }; window.clearInterval = (i) => { tm.delete(i); CI(i); };
  const hold = () => { if (fz) for (const a of document.getAnimations()) if (!seen.has(a)) { seen.set(a, null); try { a.pause(); a.currentTime = 0; } catch (e) {} } RAF(hold); };
  window.__clk = {
    freeze() { if (fz) return; vt = RN(); d0 = DN() - vt; fz = true;
      try { for (const a of document.getAnimations()) { seen.set(a, vt - (a.currentTime || 0)); a.pause(); } } catch (e) {} RAF(hold); },
    step(ms) { const start = vt, end = vt + ms;
      for (let g = 0; g < 2000; g++) { let nx = null, ni; for (const [i, t] of tm) if (t.at <= end && (!nx || t.at < nx.at)) { nx = t; ni = i; }
        if (!nx) break; vt = Math.max(vt, nx.at); if (nx.every) nx.at += nx.every; else tm.delete(ni);
        try { typeof nx.cb === 'function' ? nx.cb(...nx.a) : (0, eval)(nx.cb); } catch (e) {} }
      vt = end; const cbs = [...raf.values()]; raf.clear(); for (const cb of cbs) { try { cb(vt); } catch (e) {} }
      for (const a of document.getAnimations()) { let s = seen.get(a); if (s == null) { s = start; seen.set(a, s); }
        try { a.pause(); a.currentTime = Math.max(0, vt - s) * (a.playbackRate || 1); } catch (e) {} } },
  };
  if (window.__FREEZE_AT_START) window.__clk.freeze();
})();`;

const ARROW = `<svg xmlns="http://www.w3.org/2000/svg" width="21" height="31" viewBox="0 0 21 31"><path d="M2 1.5v24.2l5.9-5.4 4.3 9.2 3.7-1.7-4.2-9 8-.6z" fill="#000" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
const OVERLAY = `(() => { if (document.getElementById('__cur')) return; const d = document.createElement('div'); d.id = '__cur';
  d.style.cssText = 'position:fixed;left:0;top:0;width:21px;height:31px;z-index:2147483647;pointer-events:none;transform-origin:2px 2px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.35));will-change:transform';
  d.innerHTML = ${JSON.stringify(ARROW)}; document.documentElement.appendChild(d); })();`;

// find an element: {sel, nth} | {text, within} | {item} (board item id); returns its viewport rect
const FIND = `(q) => { let el = null;
  if (q.item) el = document.querySelector('.item[data-id="' + q.item + '"]' + (q.part ? ' ' + q.part : ''));
  else if (q.sel) el = document.querySelectorAll(q.sel)[q.nth || 0];
  else if (q.text) { const root = q.within ? document.querySelector(q.within) : document.body; const all = root ? root.querySelectorAll('*') : []; const hits = [];
    for (const e of all) { if (/^(SCRIPT|STYLE|NOSCRIPT)$/.test(e.tagName)) continue; const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
      if ((e.textContent || '').replace(/\\s+/g, ' ').toLowerCase().includes(q.text.toLowerCase())) hits.push(e); }
    const inner = hits.filter((e) => !hits.some((o) => o !== e && e.contains(o))); el = inner[q.nth || 0] || null; }
  if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, sy: window.scrollY }; }`;

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new',
    args: ['--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', '--force-device-scale-factor=1', '--disable-features=PaintHolding'] });
  const failed = [];
  for (const sc of spec.scenes) {
    if (only.length && !only.includes(sc.id)) continue;
    try {
    const [VW, VH] = sc.viewport || spec.viewport || [1440, 995];
    const f0 = Math.round(sc.t0 * FPS), f1 = Math.round(sc.t1 * FPS), N = f1 - f0;
    const dir = path.join(OUT, sc.id); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    const page = await browser.newPage(); await page.setViewport({ width: VW, height: VH, deviceScaleFactor: 1 });
    page.on('pageerror', (e) => console.log('  pageerror', sc.id, String(e.message).slice(0, 120)));
    const cdp = await page.createCDPSession();
    if (sc.freeze === 'start') await page.evaluateOnNewDocument('window.__FREEZE_AT_START = true;');
    await page.evaluateOnNewDocument(CLOCK);
    const find = async (q) => { const r = await page.evaluate(`(${FIND})(${JSON.stringify(q)})`); if (!r) throw new Error(`scene ${sc.id}: target not found ${JSON.stringify(q)}`);
      if (q.box) { const [a, b, c, d] = q.box; return { x: r.x + r.w * a, y: r.y + r.h * b, w: r.w * (c - a), h: r.h * (d - b), sy: r.sy }; } // part of an element, as fractions (a spot inside a screenshot)
      return r; };

    // ---- load
    let boardKeys = 0;
    if (sc.board) {
      const B = spec.board; const html = fs.readFileSync(B.html, 'utf8');
      const items = fs.readdirSync(B.items).filter((f) => f.endsWith('.json')).map((f) => Object.assign(JSON.parse(fs.readFileSync(path.join(B.items, f))), { id: f.slice(0, -5) }));
      const frames = items.filter((i) => i.type === 'frame' && typeof i.order === 'number').sort((a, b) => a.order - b.order);
      const fr = (id) => { const f = frames.find((x) => x.id === id); if (!f) throw new Error('no board section ' + id); return f; };
      const first = fr(sc.board.from || sc.board.at); if (sc.board.from) boardKeys = frames.indexOf(fr(sc.board.at)) - frames.indexOf(first);
      const stageH = VH, top = first.y - 80, fh = first.h + 80, k = clamp(Math.min((VW - 60) / first.w, (stageH - 190) / fh), 0.15, 2); // same maths as the board's focusSection
      const view = { x: (VW - first.w * k) / 2 - first.x * k, y: 70 + (stageH - 190 - fh * k) / 2 - top * k, k };
      const stub = `<script>try{localStorage.setItem('brainstorm-board-view',${JSON.stringify(JSON.stringify(view))});localStorage.setItem('brainstorm-board-lock','true')}catch(e){}
        const __I=${JSON.stringify(items)};window.claude={use:async(k)=>{if(k!=='db')throw new Error('none');return{collection:()=>({limit:()=>({onSnapshot:(cb)=>{cb({docChanges:()=>__I.map((d)=>({type:'added',doc:{id:d.id,data:()=>d}}))})}})}),
        doc:()=>({onSnapshot:(cb)=>cb({exists:true,data:()=>({title:${JSON.stringify(B.title || '')}})}),set:async()=>{},delete:async()=>{}})}}};</script>`;
      await page.setRequestInterception(true);
      page.on('request', (rq) => { const u = new URL(rq.url());
        if (u.hostname !== 'board.local') return rq.continue();
        if (u.pathname === '/') return rq.respond({ status: 200, contentType: 'text/html; charset=utf-8', body: html.replace('<div id="app">', stub + '<div id="app">') });
        const m = u.pathname.match(/^\/_blob\/([A-Za-z0-9_-]+)/); const f = m && fs.readdirSync(B.blobs).find((x) => x.startsWith(m[1]));
        if (!f) return rq.respond({ status: 404, body: '' });
        rq.respond({ status: 200, contentType: { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', svg: 'image/svg+xml' }[f.split('.').pop()] || 'application/octet-stream', body: fs.readFileSync(path.join(B.blobs, f)) }); });
      await page.goto('http://board.local/', { waitUntil: 'networkidle0' });
      await page.evaluate(() => Promise.all([document.fonts.ready, ...[...document.images].map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })))]));
    } else {
      if (sc.blockPost) { await page.setRequestInterception(true); page.on('request', (rq) => (rq.method() === 'GET' ? rq.continue() : rq.abort())); } // never let a demo form really submit
      await page.goto(sc.url || 'file://' + path.resolve(sc.file), { waitUntil: sc.freeze === 'start' ? 'load' : 'networkidle2', timeout: 60000 });
      if (sc.freeze !== 'start') { // wake lazy images, then come back
        const H = await page.evaluate(() => document.documentElement.scrollHeight);
        for (let y = 0; y < H; y += 700) { await page.evaluate((y) => window.scrollTo(0, y), y); await sleep(120); }
        await page.evaluate(() => window.scrollTo(0, 0)); await sleep(400);
      } else await sleep(sc.settle || 1500);
      if (sc.css) await page.addStyleTag({ content: sc.css });
    }
    await page.evaluate(() => window.__clk.freeze());
    const stepClock = (ms) => page.evaluate((ms) => window.__clk.step(ms), ms);

    // ---- state
    const cur = { x: (sc.mouse || [VW * 0.6, VH * 0.7])[0], y: (sc.mouse || [VW * 0.6, VH * 0.7])[1], down: false, press: 0 };
    let scrollY = 0, scrollM = null, curM = null; const typeQ = [];
    const cam = { cx: VW / 2, cy: VH / 2, w: VW, follow: false, anim: null };
    const camRect = async (c) => { // -> {cx, cy, w, follow}
      if (c === 'full' || !c) return { cx: VW / 2, cy: VH / 2, w: VW, follow: false };
      if (Array.isArray(c)) return { cx: c[0] + c[2] / 2, cy: c[1] + c[2] * AR / 2, w: c[2], follow: false };
      if (c.w && !c.sel && !c.item && !c.text) return { cx: cur.x, cy: cur.y, w: c.w, follow: true };
      const r = await find(c), pad = c.pad == null ? 40 : c.pad; const w = Math.max(r.w + pad * 2, (r.h + pad * 2) / AR, c.min || 480);
      return { cx: r.x + r.w / 2 + (c.dx || 0), cy: r.y + r.h / 2 + (c.dy || 0), w: Math.min(w, VW), follow: false };
    };
    const point = async (tg) => { if (Array.isArray(tg)) return { x: tg[0], y: tg[1] }; const r = await find(tg), at = tg.at || [0.5, 0.5]; return { x: r.x + r.w * at[0] + (tg.dx || 0), y: r.y + r.h * at[1] + (tg.dy || 0) }; };
    const travel = (a, b, dur) => { const d = Math.hypot(b.x - a.x, b.y - a.y) || 1; const bend = (rnd() - 0.5) * 0.22 * d;
      const mx = (a.x + b.x) / 2 - ((b.y - a.y) / d) * bend, my = (a.y + b.y) / 2 + ((b.x - a.x) / d) * bend;
      return { dur: dur || clamp(0.26 + d / 1500, 0.3, 1.0), at: (u) => { const s = mj(u), q = 1 - s; return { x: q * q * a.x + 2 * q * s * mx + s * s * b.x, y: q * q * a.y + 2 * q * s * my + s * s * b.y }; } }; };
    const poly = (pts) => { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
      return (u) => { const s = (0.25 * u + 0.75 * (u * u * (3 - 2 * u))) * L[L.length - 1]; let i = 1; while (i < L.length - 1 && L[i] < s) i++; const k = (s - L[i - 1]) / (L[i] - L[i - 1] || 1);
        return { x: pts[i - 1].x + (pts[i].x - pts[i - 1].x) * k, y: pts[i - 1].y + (pts[i].y - pts[i - 1].y) * k }; }; };
    const shape = async (a) => { // hand-drawn laser shapes around a target rect
      const kind = a.laser || 'line', pts = [];
      if (kind === 'line' || a.drag) { const p = await point(a.from || a.drag.from), q = await point(a.to || a.drag.to); const n = 14, w = a.drag ? 0 : 2.5, ph = rnd() * 6;
        for (let i = 0; i <= n; i++) { const u = i / n; pts.push({ x: p.x + (q.x - p.x) * u, y: p.y + (q.y - p.y) * u + Math.sin(u * 5 + ph) * w }); } return pts; }
      const r = await find(a.on), pad = a.pad == null ? 10 : a.pad;
      if (kind === 'underline') { const y = r.y + r.h + (a.gap == null ? 5 : a.gap), n = 16, ph = rnd() * 6, pass = a.times || 1;
        for (let k = 0; k < pass; k++) for (let i = 0; i <= n; i++) { const u = k % 2 ? 1 - i / n : i / n; pts.push({ x: r.x - 4 + (r.w + 8) * u, y: y + k * 5 + Math.sin(u * 6 + ph) * 2 - u * 2 }); } return pts; }
      const cx = r.x + r.w / 2, cy = r.y + r.h / 2, rx = r.w / 2 + pad, ry = r.h / 2 + pad, a0 = -2.3 + rnd() * 0.5, sweep = Math.PI * 2 * (1.06 + rnd() * 0.06), ph = rnd() * 6, n = 44;
      for (let i = 0; i <= n; i++) { const u = i / n, th = a0 + sweep * u, g = (1 + 0.035 * Math.sin(3 * th + ph)) * (1 + 0.05 * u); pts.push({ x: cx + Math.cos(th) * rx * g, y: cy + Math.sin(th) * ry * g }); }
      return pts;
    };
    const start = async (a, t) => {
      if (a.key) for (let i = 0; i < (a.times || 1); i++) await page.keyboard.press(a.key);
      if (a.eval) await page.evaluate(a.eval);
      if (a.scroll != null) { let y = a.scroll; if (typeof y === 'object') { const r = await find(y); y = r.sy + r.y - (y.top == null ? 120 : y.top); }
        const max = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight); y = clamp(y, 0, max);
        scrollM = { t0: t, dur: a.dur || clamp(0.35 + Math.abs(y - scrollY) / 2600, 0.45, 1.5), from: scrollY, to: y }; }
      if (a.cam !== undefined) { const to = await camRect(a.cam); cam.follow = to.follow;
        cam.anim = { t0: t, dur: a.dur || 0.8, from: { cx: cam.cx, cy: cam.cy, w: cam.w }, to, wOnly: to.follow }; }
      if ((a.move || a.laser || a.drag) && cur.down) { await page.mouse.up(); cur.down = false; } // a new gesture always starts with the button up, or the trip there gets drawn
      if (a.move) { const m = travel(cur, await point(a.move), a.dur); curM = { t0: t, dur: m.dur, at: m.at }; }
      if (a.laser || a.drag) { const pts = await shape(a), tr = travel(cur, pts[0], a.lead), p = poly(pts), dur = a.dur || 0.8;
        curM = { t0: t, dur: tr.dur + dur, at: (u, tt) => (tt < tr.dur ? tr.at(tt / tr.dur) : p((tt - tr.dur) / dur)), downAt: a.hover ? null : tr.dur, upAt: tr.dur + dur }; } // hover: true = trace the shape with the button up (circling something on a website with the arrow)
      if (a.click) { cur.press = 4; await page.mouse.down(); await page.mouse.up(); }
      if (a.type) { const cps = a.cps || 11; [...a.type].forEach((ch, i) => typeQ.push({ at: t + i / cps + (rnd() - 0.5) * 0.04, ch })); }
    };

    // ---- before frame 0 (not recorded)
    if (sc.board) { await page.keyboard.press('ArrowRight'); for (let i = 0; i < 24; i++) await stepClock(1000 / FPS);
      await page.keyboard.press('z'); for (let i = 0; i < 130; i++) await stepClock(1000 / FPS); }
    if (sc.scroll != null) { await start({ scroll: sc.scroll }, 0); scrollY = scrollM.to; scrollM = null; await page.evaluate((y) => window.scrollTo(0, y), scrollY); await sleep(300); }
    for (const a of sc.pre || []) { if (a.wait) { for (let i = 0; i < Math.round(a.wait * FPS); i++) await stepClock(1000 / FPS); } else { await start(a, 0); if (curM) { const p = curM.at(1, curM.dur); cur.x = p.x; cur.y = p.y; curM = null; } if (scrollM) { scrollY = scrollM.to; scrollM = null; await page.evaluate((y) => window.scrollTo(0, y), scrollY); } } }
    Object.assign(cam, await camRect(sc.cam || 'full')); cam.anim = null;
    const showCursor = sc.cursor !== 'none' && !sc.board; if (showCursor) await page.evaluate(OVERLAY).catch(() => {}); // raw XML / text documents have nothing to attach a cursor to
    await page.mouse.move(cur.x, cur.y);
    const acts = (sc.actions || []).slice().sort((a, b) => a.t - b.t); if (boardKeys > 0) acts.unshift({ t: 0.08, key: 'ArrowRight', times: boardKeys });
    let ai = 0; const t00 = Date.now();

    // ---- frames
    for (let f = 0; f < N; f++) {
      const t = f / FPS, dt = 1 / FPS;
      while (ai < acts.length && acts[ai].t <= t + 1e-6) await start(acts[ai++], t);
      while (typeQ.length && typeQ[0].at <= t) await page.keyboard.type(typeQ.shift().ch);
      if (scrollM) { const u = clamp((t - scrollM.t0) / scrollM.dur, 0, 1); scrollY = scrollM.from + (scrollM.to - scrollM.from) * ease(u); await page.evaluate((y) => window.scrollTo(0, y), scrollY); if (u >= 1) scrollM = null; }
      const sub = cur.down || (curM && curM.downAt != null) ? 3 : 1;
      for (let k = 1; k <= sub; k++) { const tt = t - dt + (dt * k) / sub + dt; // cursor position at the end of this sub-step
        if (curM) { const el = tt - curM.t0, p = curM.at(clamp(el / curM.dur, 0, 1), clamp(el, 0, curM.dur)); cur.x = p.x; cur.y = p.y;
          await page.mouse.move(cur.x, cur.y);
          if (curM.downAt != null && !cur.down && el >= curM.downAt && el < curM.upAt) { await page.mouse.down(); cur.down = true; }
          if (cur.down && el >= curM.upAt) { await page.mouse.up(); cur.down = false; }
          if (el >= curM.dur) { if (cur.down) { await page.mouse.up(); cur.down = false; } curM = null; } }
        await stepClock(1000 / FPS / sub); }
      if (showCursor) { const s = cur.press > 0 ? 0.86 : 1; cur.press--; await page.evaluate((x, y, s) => { const c = document.getElementById('__cur'); if (c) c.style.transform = `translate(${x - 2}px,${y - 2}px) scale(${s})`; }, cur.x, cur.y, s); }
      // camera
      if (cam.anim) { const u = clamp((t - cam.anim.t0) / cam.anim.dur, 0, 1), e = ease(u), A = cam.anim; cam.w = A.from.w + (A.to.w - A.from.w) * e;
        if (!A.wOnly) { cam.cx = A.from.cx + (A.to.cx - A.from.cx) * e; cam.cy = A.from.cy + (A.to.cy - A.from.cy) * e; } if (u >= 1) cam.anim = null; }
      if (cam.follow) { const hw = cam.w * 0.16, hh = cam.w * AR * 0.14; let tx = cam.cx, ty = cam.cy;
        if (cur.x > cam.cx + hw) tx = cur.x - hw; if (cur.x < cam.cx - hw) tx = cur.x + hw; if (cur.y > cam.cy + hh) ty = cur.y - hh; if (cur.y < cam.cy - hh) ty = cur.y + hh;
        const g = 1 - Math.exp(-dt / 0.22); cam.cx += (tx - cam.cx) * g; cam.cy += (ty - cam.cy) * g; }
      const w = clamp(cam.w, 200, VW), h = w * AR, x = clamp(cam.cx - w / 2, 0, VW - w), y = clamp(cam.cy - h / 2, 0, VH - h);
      const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, clip: { x, y: y + scrollY /* clip is in document coordinates */, width: w, height: h, scale: PW / w }, captureBeyondViewport: false, optimizeForSpeed: true });
      fs.writeFileSync(path.join(dir, `f${String(f).padStart(5, '0')}.jpg`), Buffer.from(shot.data, 'base64'));
    }
    console.log(`${sc.id}: ${N} frames in ${((Date.now() - t00) / 1000).toFixed(0)}s`);
    await page.close();
    } catch (e) { failed.push(sc.id); console.log(`${sc.id}: FAILED ${e.message}`); }
  }
  await browser.close(); if (failed.length) { console.log('failed scenes:', failed.join(' ')); process.exit(1); }
})().catch((e) => { console.error(e); process.exit(1); });
