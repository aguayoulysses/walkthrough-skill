---
name: walkthrough
description: Build a split-screen "application" walkthrough reel for a prospect - Ulysses's face on top the whole time, a fake desktop screen recording underneath that walks the audit board with the laser, his old site and the new site, timed to his words. Use when he says /walkthrough, "do the split screen walkthrough", "walk them through the board", "same format as Viva El Volt", or hands over camera clips plus an audit board link and asks for the screen part to be created because it was not recorded.
---

# /walkthrough - split-screen audit walkthrough

He films himself talking to camera while clicking through the prospect's audit board and sites, but the screen is NOT recorded. This skill cuts his takes and manufactures the screen half so it looks like a real screen recording: real pages, a mouse that moves like a hand, the board's own laser. First one built Oct 5 2026 for Viva El Volt (`~/Downloads/Viva El Volt walkthrough final.mp4`). Worked files for that video are in `assets/example-viva/` - start from them.

Everything renders locally. Scripts live in `~/.claude/skills/walkthrough/scripts` (`$S`). Work in a scratch folder (`$W`), never in Downloads.

## The format (do not change without him asking)
- 1080x1920, 29.97. Face on TOP (1080x1174), screen on the BOTTOM (1080x746). This matches the split he cuts by hand in his own hook. His face is on screen for the whole video.
- His finished hook (he sends it, e.g. `~/Downloads/intro hook .mov`) goes in front untouched, captions added.
- Every example is the DESKTOP view. Never a phone mock, never a floating card.
- Board sections get the board's real laser (circle, underline, line). Websites get a normal arrow cursor that hovers, clicks, types and drag-selects.
- Captions: plain white native style (`assets/caption.html`), 2-4 words. They must NEVER touch his face (he rejected y 900 on Oct 5 2026: "the subtitles are in my face"). Body: `caps_y` 990, just above the seam, well under his chin. Hook: `caps_y_hook` 1350, because his face fills the middle of the frame in the hook's full-screen shots. Look at a hook frame and a body frame with a caption on before calling it done. No hook text, no tags, no CTA card, no music.
- Camera mic is one channel only: the voice is copied to both sides in `compose.py`.
- When he says to reuse audio from an earlier video (lines that never name the client: title tag, H1, NAP, one page per service, map embed, schema, sitemap/robots), that audio plays as voiceover over the new site and his face is the "working" b-roll clip. He does NOT want llms.txt mentioned (Oct 5 2026).

## 0. Inputs
- Camera clips: the SD card mounts at `/Volumes/EOS_DIGITAL/DCIM/100CANON`. The camera clock is wrong (it said Feb 2026 in Oct 2026), so take the highest-numbered `MVI_*.MP4` files, not the newest dates. They are 4K with a 90 degree rotation flag (ffmpeg rotates them to 2160x3840 on its own) and the mic is on the RIGHT channel only.
- Make a thumbnail of each clip first. Talking clips face the lens; the side-angle clips with no speech are the "working" b-roll.
- The audit board link (claude.ai artifact), the prospect's current site, the new site's live URL.
- Earlier audio to reuse: yesterday's raw file and its ranges. Top Sky source `~/Downloads/claude please cut .mov`, ranges in `assets/example-viva/edl.json` (segments Y1-Y9).

## 1. Transcribe with real word times
whisper-cli word times are useless on these clips: he clicks and types between sentences and long silences smear the timestamps (the first Viva cut kept mouse clicks as "speech"). Use mlx-whisper:
```
ffmpeg -y -i CLIP.MP4 -ac 1 -ar 16000 -c:a pcm_s16le c.wav
uvx --python 3.12 --from mlx-whisper mlx_whisper c.wav --model mlx-community/whisper-small-mlx --language en --word-timestamps True --output-format json --output-dir mlx --condition-on-previous-text False
```
About 45 s per 4.5 min clip. Print the words with start-end times and read all of it.

## 2. Pick takes -> `edl.json` -> `cut.py`
He repeats lines until he likes one: keep the LAST clean take of each. Drop fumbles and anything he corrects ("pulls data from Bing" -> the corrected take right after).
- One segment = one unbroken run of words. `a` = first word's start, `b` = last word's end. End the segment wherever there is a pause over about 0.5 s and start a new one after it.
- A word that follows or precedes a pause gets a stretched time (`problem@91.84-93.86`). Trust the side next to the neighbouring word and estimate the other (a short word is 0.2-0.5 s). If unsure, print 20 ms RMS around it.
- `"face": {"src": "W", "a": 50}` puts the b-roll clip on camera for that segment; later segments with `{"src": "W"}` continue it. Look at a strip of the b-roll and avoid moments like drinking water.
- Face crop is `2160:2348:0:<y>` with y = eye height in the rotated frame minus about 920.
```
python3 $S/cut.py edl.json        # -> face.mp4, voice.wav, timeline.json, words_final.json (about 2.5 min from the SD card)
```
VERIFY before anything else: transcribe `voice.wav` with the same mlx command and read it as one script. Every sentence must be whole and in order. Fix the EDL and rerun until it reads clean (Viva needed two passes: a clipped "GMB").

## 3. Get the board locally
The board is a claude.ai artifact whose notes live in its database.
- `Artifact read` the link: the saved HTML is the board app. Copy it to `$W/board/board.html`.
- `ArtifactData list` collection `items` with `out_dir` -> `$W/board/items/*.json`.
- Images: the audit's `mkboard.py` maps asset ids to files in `<audit>/proof/`; copy each as `$W/board/blob/<assetid>.<ext>`. Anything not there: `Artifact read` with `path` = the asset id (one call per asset; `paths` does not take asset ids).
- Print the sections in order (frames sorted by `order`) with their note texts, and make a gridded sheet of every image so laser targets can be given as fractions of the image (`box: [x0, y0, x1, y1]`).

## 4. Script the screen -> `scenes.py` -> `screen.json` -> `rec.js`
Copy `assets/example-viva/scenes.py` and rewrite the scenes. `T('B5b', 'second', off=-0.2)` gives the final-video time of a word, so every move lands on the word that names it. Scenes must tile the body with no gaps (the script asserts it).

Scene kinds:
- `board: {at: 'f05-f', from: 'f04-f'}`: the real board with the laser tool on. With `from`, the scene opens on the previous section and pans to this one the way the arrow key does. Start lasers at least 0.7 s in, after the pan.
- `url`: a live page at desktop size (`viewport: [1280, 884]`). `freeze: 'start'` records the page's entrance animation from frame 0. `blockPost: true` on anything with a form.
- `file`: a local page. `mkvs.py <url> vs.html` = a view-source look-alike of the real HTML with ids on the title, h1, map iframe and JSON-LD lines. `mkcode.py <file> code.html` = the real build file typing itself into an editor, for the "building it" beat.
Use `node $S/fullpage.js <url> out.jpg` to get a full-page shot plus every section's offset before scripting a site.

Actions (t in final-video seconds; `scenes.py` converts):
- `move` to `[x, y]` | `{sel, nth, at: [fx, fy], dx, dy}` | `{text, within}` | `{item, part, box}`
- `laser`: `circle` / `underline` (`times: 2` goes back and forth) on a target, or `line` from/to. Add `hover: true` on a website so the arrow traces the shape without pressing (that is how to circle an image). `drag` from/to = drag-select on a website.
- `scroll` to y or to a target (`top` = how far below the top edge it lands), `click`, `type` (+`cps`), `key`, `eval`
- `cam`: `'full'`, `{w: 900}` (zoom that follows the cursor), or a target with `pad` (fixed framing). Zoom in whenever text matters; the panel is only 746 px tall. Set a fixed `cam` only AFTER a scroll has finished, the target is measured when the action starts.
```
python3 scenes.py && node $S/rec.js screen.json            # all scenes, about 15 frames/s
node $S/rec.js screen.json old new                         # just these
python3 $S/sheet.py screen/old 30 qa/old.jpg 5 400         # LOOK at every scene before composing
```
A scene that fails (target not found) is reported and skipped; fix and rerun that scene only.

Rules that came out of the first build:
- NEVER click a real submit button. Fill the form, hover the button, stop. Keep `blockPost` on.
- Do not click things that open modals on the prospect's site (the dialog rendered as a grey veil). Hover instead.
- Two laser actions must not overlap in time, or give the first a shorter `dur`.
- Old-site forms have hidden honeypot inputs: target `input[name=name]`, not the first input.
- The map embed, sitemap.xml and robots.txt all render in headless Chrome. robots.txt has the AI bot lines to select on "AI crawlers".
- Point at what he MEANS, not the nearest text. "This is AI generated" on a prospect's site is about the hero image / mascot art, so circle the image (he corrected a headline highlight on Oct 5 2026). If a line could refer to two things on screen, pick the visual one or ask.
- When he talks about the texts a form sends (customer confirmation, owner alert), show them: `assets/texts.html` renders both as desktop Messages windows. Use the REAL template wording from `~/Projects/happy-mouths/app/api/lead/[slug]/route.ts` with the prospect's name and the same fake lead typed into the form (555 number). Zoom the camera on each bubble as it arrives (`cam: [58, 60, 580]` then `[642, 60, 580]`).
- Section order he talks in is not always the board order, and some sections are never mentioned: skip those.

## 5. Captions
```
python3 $S/captions.py words_final.json states.json fixes.json     # prints every line: read them
node $S/render_caps.js states.json caps $S/../assets/caption.html
$S/caps2mov.sh caps caps.mov
```
`fixes.json` = `[[heard, meant], ...]`: brand names ("Vivald Volt" -> the real name), "being" -> "Bing", "speed delete" -> "speed to lead", and first words lost at a cut ("can see that the second" -> "You can see that the second").

## 6. Compose + QA
```
python3 $S/compose.py compose.json        # {"hook", "face", "voice", "screen": "screen.json", "caps", "caps_y": 990, "caps_y_hook": 1350, "out": "~/Downloads/<Client> walkthrough final.mp4"}
python3 $S/sheet.py "<out>" 180 qa/final.jpg 8 250
```
Check on the sheet: face top / screen bottom on every tile, no caption over his face on any tile (hook included), caption matches what the screen shows, no blank or grey screen. Check the audio: both channels the same level (`channelsplit` + `volumedetect`), zero packet gaps over 23.5 ms, about -14 LUFS. Frame count must equal hook frames + body frames. `open` the file.

## Gotchas
- Chrome's clip rounding leaves some frames 1 px off. `compose.py` re-encodes each scene to the exact panel size first; feeding the raw JPG sequence into the main graph silently dropped 12 s and drifted the captions.
- Screenshot `clip` is in document coordinates: add scrollY (rec.js does). Without it every scrolled frame is blank.
- The page clock is frozen and stepped per frame. CSS animations are driven through `document.getAnimations()`; a page `<video>` would not follow.
- The board runs from the saved HTML with a stubbed database, images served from `blob/`. It shows "Locked" and the laser tool lit, like when he presents.
- ffmpeg here has no drawtext; all text goes through Chrome.
- `uvx` downloads mlx-whisper on first use; the model is already cached.

## Voice cleanup (standard step, Oct 12 2026)
Before mixing music/sfx, clean his voice with the voice-cleanup skill: `sh $S/clean_voice.sh <cut video or wav> <voice-clean.wav>` (live-channel pick, DeepFilterNet capped at 20 dB, EQ for the boxy camera mic, de-ess, 3:1 compression). Cut on the RAW audio first so timings stay exact; master loudnorm -14 LUFS last. Keep music 22-25 dB under the voice and sfx soft (his Oct 12 2026 feedback: music and effects were too loud). One-time setup for DeepFilterNet is in the repo README.
