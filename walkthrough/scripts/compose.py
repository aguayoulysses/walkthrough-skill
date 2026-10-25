#!/usr/bin/env python3
"""compose.py spec.json   stacks face (top) over screen (bottom), puts the finished hook in front, burns captions, makes the mono mic play on both sides.
spec: {"hook": "/path/intro hook.mov" | null, "face": "face.mp4", "voice": "voice.wav", "screen": "screen.json", "caps": "caps.mov", "caps_y": 990, "caps_y_hook": 1350,
       "out": "~/Downloads/name final.mp4", "face_vf": "eq=gamma=1.08" (optional grade on the face only)}"""
import json, sys, os, subprocess, glob, shutil
S = json.load(open(sys.argv[1])); FPS = '30000/1001'; out = os.path.expanduser(S['out'])
def run(c): subprocess.run(c, check=True)
def dur(p): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))
scr = json.load(open(S['screen'])); PW, PH = scr.get('panel', [1080, 746])
shutil.rmtree('scr', ignore_errors=True); os.makedirs('scr'); n = 0; lst = []
for sc in scr['scenes']:                                  # each scene -> one clip at exactly the panel size (Chrome's clip rounding leaves some frames 1 px off, which resets ffmpeg mid-stream)
    fs = sorted(glob.glob(os.path.join(scr['out'], sc['id'], 'f*.jpg'))); want = round(sc['t1'] * 30000 / 1001) - round(sc['t0'] * 30000 / 1001)
    assert len(fs) == want, f"scene {sc['id']}: {len(fs)} frames on disk, need {want}. Re-record it."
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', FPS, '-i', os.path.join(scr['out'], sc['id'], 'f%05d.jpg'), '-vf', f'scale={PW}:{PH}:flags=lanczos,setsar=1,format=yuv420p',
         '-frames:v', str(want), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-video_track_timescale', '30000', f"scr/{sc['id']}.mp4"])
    lst.append(f"file '{sc['id']}.mp4'\n"); n += want
open('scr/list.txt', 'w').write(''.join(lst))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'scr/list.txt', '-c', 'copy', 'screen.mp4'])
PTS = 'setpts=N/(30000/1001)/TB'                            # count frames, ignore container timestamps: stitched parts drift otherwise
body = f"[0:v]{PTS},{S.get('face_vf', 'null')},setsar=1[f];[1:v]{PTS},setsar=1[s];[f][s]vstack=inputs=2,format=yuv420p[body]"
ins = ['-i', S['face'], '-i', 'screen.mp4']; k = 2; last = '[body]'
if S.get('hook'):
    ins += ['-i', os.path.expanduser(S['hook'])]; body += f";[{k}:v]fps={FPS},{PTS},scale=1080:1920,setsar=1,format=yuv420p[h];[h][body]concat=n=2:v=1:a=0[all]"; last = '[all]'; k += 1
if S.get('caps'):
    # captions never sit on his face: low on the chest in the split body, lower still while the hook is full-frame (his face fills the middle there)
    hd = dur(os.path.expanduser(S['hook'])) if S.get('hook') else 0
    ins += ['-i', S['caps']]; body += f";[{k}:v]format=rgba[c];{last}[c]overlay=x=0:y='if(lt(t,{hd:.4f}),{S.get('caps_y_hook', 1350)},{S.get('caps_y', 990)})':eof_action=pass[v]"; last = '[v]'
run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', body, '-map', last, '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', FPS, 'video_only.mp4'])
# audio in its own pass (mixing it inside the video graph has dropped packets before): voice = one mic copied to both sides, levelled; hook keeps its own mix
norm = 'highpass=f=70,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000'
if S.get('hook'):
    run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.expanduser(S['hook']), '-i', S['voice'], '-filter_complex',
         f"[0:a]aformat=channel_layouts=stereo,{norm}[a0];[1:a]pan=mono|c0=c0,{norm},pan=stereo|c0=c0|c1=c0[a1];[a0][a1]concat=n=2:v=0:a=1,aresample=async=1[a]", '-map', '[a]', '-c:a', 'pcm_s16le', 'mix.wav'])
else:
    run(['ffmpeg', '-v', 'error', '-y', '-i', S['voice'], '-af', f"pan=mono|c0=c0,{norm},pan=stereo|c0=c0|c1=c0", '-c:a', 'pcm_s16le', 'mix.wav'])
dv, da = dur('video_only.mp4'), dur('mix.wav'); print('frames in:', n, 'video', round(dv, 2), 'audio', round(da, 2)); assert abs(dv - da) < 0.12, f'video {dv:.2f}s vs audio {da:.2f}s'
run(['ffmpeg', '-v', 'error', '-y', '-i', 'video_only.mp4', '-i', 'mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out])
print('wrote', out, f'{dv:.2f}s')
