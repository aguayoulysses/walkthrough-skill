# /walkthrough - split-screen audit walkthrough reel

A Claude Code skill that turns raw talking-head camera clips plus an audit board link into a finished 1080x1920 reel: the presenter's face on top the whole time, and a fake desktop screen recording underneath that walks the audit board with its laser, the prospect's old site and the new site, timed to the spoken words.

The screen half is never recorded. The skill manufactures it in headless Chrome: real pages, a mouse that moves like a hand, the board's own laser, a virtual camera that zooms where the text matters. Captions are rendered in Chrome too and composited over the seam.

The full method, the format rules, every scene action and the QA checklist are in `walkthrough/SKILL.md`. Read it top to bottom before the first build.

## Install

```
git clone https://github.com/aguayoulysses/walkthrough-skill.git
cp -R walkthrough-skill/walkthrough ~/.claude/skills/walkthrough
cd ~/.claude/skills/walkthrough/scripts && npm install
```

Then in Claude Code say `/walkthrough` and hand it the camera clips, the audit board link, the old site URL and the new site URL.

## Requirements (macOS)

- Google Chrome installed at `/Applications/Google Chrome.app` (the recorder and caption renderer launch it headless).
- Node 18 or newer. `npm install` inside `walkthrough/scripts` pulls `puppeteer-core`.
- ffmpeg and ffprobe (`brew install ffmpeg`).
- Python 3.
- `uv` (`brew install uv`). Transcription runs `mlx-whisper` through `uvx`, which downloads it on first use. Apple Silicon only.
- DeepFilterNet for the voice cleanup step, one time:

```
mkdir -p ~/.local/share/voice-cleanup && cd ~/.local/share/voice-cleanup
uv venv -p 3.11 venv && . venv/bin/activate
uv pip install deepfilternet torch==2.2.2 torchaudio==2.2.2 "numpy<2" soundfile
```

torch 2.2.2 and numpy below 2 are pinned because deepfilternet imports an old torchaudio path.

## What is in here

```
walkthrough/
  SKILL.md                  the skill: format, pipeline, rules, gotchas
  scripts/
    cut.py                  EDL -> face.mp4, voice.wav, timeline.json, words_final.json
    rec.js                  fake screen recording in headless Chrome (board laser, cursor, zoom camera)
    fullpage.js             full-page screenshot helper
    mkvs.py / mkcode.py     view-source and code panes for the screen half
    captions.py             word times -> caption states
    render_caps.js          caption PNGs (uses assets/caption.html)
    caps2mov.sh             caption PNGs -> ProRes 4444 overlay
    clean_voice.sh          voice cleanup: channel pick, DeepFilterNet, EQ, de-ess, compression
    compose.py              hook + face + screen + captions -> final mp4
    sheet.py                contact sheet for QA
    package.json
  assets/
    caption.html            native white caption style
    texts.html              the two SMS windows (customer confirmation, owner alert)
    example-viva/           the first build (Oct 2026): edl.json, scenes.py, fixes.json, compose.json
```

## Making it yours

SKILL.md was written for one presenter and his sites, so a few things are personal:

- The face crop, the SD card path and the right-channel mic are his camera setup. Adjust `crop`, `ch` and the clip source in your `edl.json`.
- The SMS windows in `assets/texts.html` quote his lead-form templates. Swap in your own wording.
- The example in `assets/example-viva/` is a real prospect build. Copy it as a starting point and change the URLs, segments and scenes.

Start every new build from the example folder, keep the format rules in SKILL.md, and look at the contact sheets before calling anything done.
