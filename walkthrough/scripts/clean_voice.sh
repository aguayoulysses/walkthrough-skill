#!/bin/sh
# Voice cleanup SOP (Oct 12 2026). Usage: clean_voice.sh <input video or audio> <output.wav> [atten_dB]
# Output: 48 kHz stereo 16-bit WAV of the cleaned voice, same length as the input, NOT loudness-normalized
# (master with loudnorm -14 LUFS at the very end, after music and sfx are mixed).
set -e
IN="$1"; OUT="$2"; ATTEN="${3:-20}"
[ -f "$IN" ] && [ -n "$OUT" ] || { echo "usage: clean_voice.sh <input> <output.wav> [atten_dB]"; exit 1; }
VENV="$HOME/.local/share/voice-cleanup/venv"
[ -x "$VENV/bin/deepFilter" ] || { echo "DeepFilterNet missing: see SKILL.md setup"; exit 1; }
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT

# 1. Pick the channel(s). Camera mics often record on ONE side only; never average a dead channel in.
L=$(ffmpeg -hide_banner -i "$IN" -vn -af "pan=mono|c0=c0,volumedetect" -f null - 2>&1 | grep -oE 'mean_volume: [-0-9.]+' | awk '{print $2}')
R=$(ffmpeg -hide_banner -i "$IN" -vn -af "pan=mono|c0=c1,volumedetect" -f null - 2>&1 | grep -oE 'mean_volume: [-0-9.]+' | awk '{print $2}')
PAN=$(python3 -c "
l=float('${L:--99}' or -99); r=float('${R:--99}' or -99)
print('pan=mono|c0=c0' if l-r>10 else 'pan=mono|c0=c1' if r-l>10 else 'pan=mono|c0=0.5*c0+0.5*c1')")
echo "channels: L ${L:-none} dB, R ${R:-none} dB -> $PAN"
ffmpeg -v error -y -i "$IN" -vn -af "$PAN" -ar 48000 -c:a pcm_s24le "$W/raw.wav"

# 2. AI noise + room cleanup. Attenuation is capped (default 20 dB) so the voice never turns robotic.
"$VENV/bin/deepFilter" "$W/raw.wav" --atten-lim "$ATTEN" -o "$W" >/dev/null 2>&1
DF="$W/raw_DeepFilterNet3.wav"

# 3. Tone + dynamics: rumble out, boxy low-mids down, a little warmth, clarity and air up,
#    soft de-ess, gentle 3:1 compression, safety limiter.
ffmpeg -v error -y -i "$DF" -af "highpass=f=80:poles=2,equalizer=f=320:t=q:w=1.1:g=-4,equalizer=f=140:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.2:g=4,equalizer=f=9000:t=h:w=2000:g=2,deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=4dB:knee=4,alimiter=limit=0.89:level=false" -ar 48000 -ac 2 -c:a pcm_s16le "$OUT"

# 4. Report: length must match, tone should move from mud to presence.
meas() { ffmpeg -ss 5 -t 20 -i "$1" -af "$2,volumedetect" -f null - 2>&1 | grep -oE 'mean_volume: [-0-9.]+' | awk '{print $2}'; }
echo "length in/out: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/raw.wav") / $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
echo "low-mid 200-500 Hz: $(meas "$W/raw.wav" 'highpass=f=200,lowpass=f=500') -> $(meas "$OUT" 'highpass=f=200,lowpass=f=500') dB"
echo "presence 2.5-5 kHz: $(meas "$W/raw.wav" 'highpass=f=2500,lowpass=f=5000') -> $(meas "$OUT" 'highpass=f=2500,lowpass=f=5000') dB"
echo "done: $OUT"
