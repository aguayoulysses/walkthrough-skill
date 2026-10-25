#!/usr/bin/env python3
"""sheet.py <frames_dir | video> <every_n_frames> <out.jpg> [cols=4] [tile_w=480]   contact sheet to LOOK at before calling a scene done"""
import sys, os, glob, subprocess, tempfile
from PIL import Image, ImageDraw
src, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4; tw = int(sys.argv[5]) if len(sys.argv) > 5 else 480
if os.path.isdir(src): fs = sorted(glob.glob(src + '/f*.jpg'))[::n]; labels = [str(i * n) for i in range(len(fs))]
else:
    d = tempfile.mkdtemp(); subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f"select='not(mod(n,{n}))',scale={tw}:-2", '-fps_mode', 'vfr', '-q:v', '4', d + '/f%05d.jpg'], check=True)
    fs = sorted(glob.glob(d + '/f*.jpg')); labels = ['%.1fs' % (i * n / 29.97) for i in range(len(fs))]
ims = [Image.open(f).convert('RGB') for f in fs]; th = round(tw * ims[0].height / ims[0].width); rows = -(-len(ims) // cols)
S = Image.new('RGB', (cols * tw, rows * th), 'black'); D = ImageDraw.Draw(S)
for i, im in enumerate(ims):
    x, y = (i % cols) * tw, (i // cols) * th; S.paste(im.resize((tw, th)), (x, y)); D.rectangle([x, y, x + 46, y + 13], fill='black'); D.text((x + 3, y + 1), labels[i], fill='yellow')
S.save(out, quality=80); print(out, len(ims), 'tiles')
