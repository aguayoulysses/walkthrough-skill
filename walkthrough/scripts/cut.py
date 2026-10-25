#!/usr/bin/env python3
"""cut.py edl.json  ->  timeline.json, face.mp4 (1080x1174), voice.wav (mono mic on both sides), words_final.json

Turns the EDL (which takes to keep, in order) into the talking-head half of the split screen.
A segment is one unbroken run of words: a = start of its first word, b = end of its last word, both read off the
word-level transcript. To drop a pause or a fumbled word, end the segment and start a new one (that is the jump cut).

edl.json:
{ "fps": 29.97002997,
  "face": [1080, 1174],                         # top panel size
  "sources": { "A": {"path": ".../MVI_7460.MP4", "wav": "sd/7460.wav", "words": "sd/w7460.json",
                     "ch": "R",                 # which channel has the mic: L, R or both
                     "crop": "2160:2348:0:240", # region of the (rotated) frame that becomes the face panel
                     "gain": 0 } },
  "segments": [ {"id": "S1", "src": "A", "a": 50.0, "b": 54.0},                 # optional "lead" (0.07) / "tail" (0.13) seconds of air
                {"id": "Y1", "src": "Y", "a": 106.97, "b": 108.41,
                 "face": {"src": "W", "a": 20.0}}                                   # b-roll on camera, this audio as voiceover
              ] }
"face": {"src": "W"} with no "a" continues the b-roll from where the last b-roll segment stopped.
Segments with "src" whose source has "raw": true are passed through untouched by compose (the finished hook).
"""
import json, sys, os, subprocess

E = json.load(open(sys.argv[1]))
FPS = E.get('fps', 30000 / 1001)
FW, FH = E.get('face', [1080, 1174])
os.makedirs('parts', exist_ok=True)

def load_words(S):
    """word list [(text, start, end)] in source seconds, from mlx_whisper --word-timestamps json (see SKILL.md step 1)."""
    if not S.get('words'): return []
    J = json.load(open(S['words'])); off = S.get('words_offset', 0)
    return [(w['word'].strip(), w['start'] + off, w['end'] + off) for g in J['segments'] for w in g.get('words', [])]

def pieces(seg):
    # a = start of the first word, b = end of the last word, straight from the word-level transcript.
    return [(max(0, seg['a'] - seg.get('lead', 0.07)), seg['b'] + seg.get('tail', 0.13))]

def run(cmd): subprocess.run(cmd, check=True)

timeline = []; t = 0.0; n = 0; broll_pos = {}; vlist = []; alist = []; words = []
for seg in E['segments']:
    S = E['sources'][seg['src']]
    if S.get('raw'):
        d = seg['b'] - seg['a']; fr = round(d * FPS)
        timeline.append({'id': seg['id'], 'raw': True, 'src': seg['src'], 't0': t, 't1': t + fr / FPS, 'pieces': [[seg['a'], seg['b'], t]]})
        for w, ws, we in load_words(S):
            if seg['a'] <= ws < seg['b']: words.append({'w': w, 's': t + ws - seg['a'], 'e': t + we - seg['a'], 'seg': seg['id']})
        t += fr / FPS; continue
    ps = pieces(seg); t0 = t; rec = []
    W = load_words(S)
    for a, b in ps:
        fa = round(a * FPS); fn = max(2, round((b - a) * FPS)); a = fa / FPS; d = fn / FPS
        face = seg.get('face'); fsrc, fa_t = seg['src'], a
        if face:
            fsrc = face['src']; fa_t = face['a'] if 'a' in face and not rec else broll_pos.get(fsrc, face.get('a', 0))
            fa_t = round(fa_t * FPS) / FPS; broll_pos[fsrc] = fa_t + d
        F = E['sources'][fsrc]
        vp, ap = f'parts/v{n:03d}.mp4', f'parts/a{n:03d}.wav'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{fa_t:.5f}', '-i', F['path'], '-frames:v', str(fn), '-an',
             '-vf', f"crop={F['crop']},scale={FW}:{FH}:flags=lanczos,fps=30000/1001,setsar=1" + (',' + F['vf'] if F.get('vf') else ''),
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-video_track_timescale', '30000', vp])
        ch = {'L': 'pan=mono|c0=c0', 'R': 'pan=mono|c0=c1'}.get(S.get('ch', 'both'), 'pan=mono|c0=0.5*c0+0.5*c1')
        fade = f"afade=t=in:d=0.015,afade=t=out:st={d - 0.02:.4f}:d=0.02"
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.5f}', '-i', S['path'], '-t', f'{d:.5f}', '-vn',
             '-af', f"{ch},volume={S.get('gain', 0)}dB,{fade},aresample=48000,apad=whole_dur={d:.5f}", '-t', f'{d:.5f}', '-c:a', 'pcm_s16le', ap])
        vlist.append(vp); alist.append(ap)
        for w, ws, we in W:
            if seg['a'] - 0.3 <= ws < seg['b'] - 0.02 and we > seg['a'] + 0.02:
                words.append({'w': w, 's': round(t + max(0, ws - a), 3), 'e': round(t + min(d, we - a), 3), 'seg': seg['id']})
        rec.append([round(a, 3), round(a + d, 3), round(t, 4)]); t += d; n += 1
    timeline.append({'id': seg['id'], 'src': seg['src'], 't0': round(t0, 4), 't1': round(t, 4), 'pieces': rec, 'face': seg.get('face', {}).get('src')})

open('parts/v.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in vlist))
open('parts/a.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in alist))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'parts/v.txt', '-c', 'copy', 'face.mp4'])
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'parts/a.txt', '-c:a', 'pcm_s16le', 'voice.wav'])
json.dump({'fps': FPS, 'duration': round(t, 4), 'segments': timeline}, open('timeline.json', 'w'), indent=1)
json.dump(words, open('words_final.json', 'w'))
for s in timeline:
    ws = ' '.join(w['w'] for w in words if w['seg'] == s['id'])
    print(f"{s['id']:>6} {s['t0']:7.2f}-{s['t1']:7.2f} ({s['t1'] - s['t0']:5.2f}s, {len(s['pieces'])} pc) {ws[:110]}")
print('total', round(t, 2))
