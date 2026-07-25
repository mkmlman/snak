# Snak

**Neighbour-ready spoken Danish.** English bridges, Roman only, Copenhagen register.

Short lessons for speak + understand — hello through clock time. Built for the person who lives here and wants to sound like it.

## Design

Warm parchment `#f5f4ed`, ink blue `#1B365D` as the sole accent, serif-led hierarchy (Charter). The [Kami](https://github.com/tw93/Kami) constraint system for printed matter, applied to courseware.

No dark mode, no script, no exams. Every page reads like a composed document, not a dashboard.

## Course

9 lessons + 9 reference sheets, one skill each:

| # | Lesson | Reference |
|---|--------|-----------|
| 0001 | Greet a neighbour | Polite check-in |
| 0002 | Where are you going? | Where-going |
| 0003 | How much? (Hvor meget + 1–10) | Prices + numbers |
| 0004 | Directions — left, right, straight | Directions |
| 0005 | Ordering food at a cafe | Food ordering |
| 0006 | Excuse me, help, sorry | Survival politeness |
| 0007 | Time-of-day greetings | Time greetings |
| 0008 | Numbers 11–20 | Numbers 11–20 |
| 0009 | What time? (clock time) | Clock time |

Each lesson has: phrase cards, model dialogue, retrieval quiz, production practice, and a real-world task.

## Audio

Browser-generated Danish (Web Speech API) — click the speaker icon next to any phrase. A **slow** option is available for all phrases. Requires a system Danish voice.

> If you prefer static audio files (offline use, consistent quality): install `edge-tts`, run the previous version of `tools/gen_audio.py` (which includes TTS generation) to produce MP3s and reinject `<audio>` controls.

## Run

```bash
python3 -m http.server 8788 -d docs
```

No build step, no dependencies. Open `http://localhost:8788`.

### Prepare pages

```bash
uv run tools/gen_audio.py
```

Strips any stale audio blocks and injects the `speak.js` script. Run after editing lesson or reference HTML.

## Stack

- Static HTML + CSS (Kami palette in `assets/lesson.css`)
- Python 3.13 · `uv` · `edge-tts` *(all optional — only needed for page preparation or static audio generation)*
- Zero frameworks, zero build tools
