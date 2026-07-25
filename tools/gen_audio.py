#!/usr/bin/env python3
"""Generate TTS audio and inject audio blocks into lesson/reference HTML.

Usage: uv run tools/gen_audio.py
"""

import asyncio
import re
import unicodedata
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
PUBLISH = ROOT / "docs"
AUDIO_DIR = PUBLISH / "assets" / "audio"
VOICE = "da-DK-ChristelNeural"
LESSONS_DIR = PUBLISH / "lessons"
REFERENCE_DIR = PUBLISH / "reference"

AUDIO_DISCLAIMER = """\
      <div class="audio-disclaimer" role="note">
        <strong>Audio:</strong> Machine-generated Danish (edge-tts · da-DK-ChristelNeural).
        Helpful for rhythm and recognition — may not perfectly match native Copenhagen pronunciation.
        Prefer what you hear from neighbours when the two differ.
      </div>"""


# ── Helpers ───────────────────────────────────────────────────────────


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9']+", "_", s)
    return s.strip("_") or "audio"


# ── Step 1: build a text→slug map from all HTML files ────────────────


def iter_texts(html: str):
    for tag in ("p", "span", "td"):
        for m in re.finditer(
            rf'<{tag}\s+class="da">(.*?)</{tag}>', html, re.DOTALL
        ):
            yield strip_tags(m.group(1)), "da"
    for m in re.finditer(
        r'<span\s+class="line">(.*?)</span>', html, re.DOTALL
    ):
        yield strip_tags(m.group(1)), "line"


def build_phrase_map() -> dict:
    used = {}
    phrase_map = {}

    for d in (LESSONS_DIR, REFERENCE_DIR):
        for fp in sorted(d.glob("*.html")):
            html = fp.read_text(encoding="utf-8")
            for text, tag in iter_texts(html):
                if not text or text in ("…", "—"):
                    continue
                base = slugify(text)
                slug = base
                i = 2
                while slug in used and used[slug] != text:
                    slug = f"{base}_{i}"
                    i += 1
                used[slug] = text
                phrase_map[text] = {
                    "slug": slug,
                    "pair": tag == "line",
                }
    return phrase_map


# ── Step 2: generate audio files ──────────────────────────────────────


async def gen_one(slug: str, text: str, suffix: str = "") -> Path | None:
    fname = f"{slug}{suffix}.mp3"
    fpath = AUDIO_DIR / fname
    if fpath.exists() and fpath.stat().st_size > 0:
        return fpath
    if fpath.exists() and fpath.stat().st_size == 0:
        fpath.unlink()
    clean = text.replace("…", "...").replace("—", " — ")
    if not clean.strip():
        return None
    rate = "-20%" if suffix == "_slow" else "+0%"
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(clean, VOICE, rate=rate)
            await communicate.save(str(fpath))
            print(f"  OK {fname}", flush=True)
            return fpath
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2)
                continue
            print(f"  FAIL {fname}: {e}", flush=True)
            return None


async def gen_all(phrase_map: dict):
    done = set()
    total = len(phrase_map)
    for i, (text, info) in enumerate(phrase_map.items(), 1):
        slug = info["slug"]
        if slug in done:
            continue
        done.add(slug)
        print(f"[{i}/{total}] {slug}...", flush=True)
        for suffix in ("", "_slow", "_nat"):
            await gen_one(slug, text, suffix)
            await asyncio.sleep(1.5)


# ── Step 3: inject audio blocks into HTML ─────────────────────────────


def ablock(slug: str, pair: bool) -> str:
    if pair:
        return (
            f'<div class="audio-block" data-slug="{slug}">'
            f'<span class="audio-pair">'
            f'<span class="audio-label">slow</span>'
            f'<audio controls preload="none" '
            f'src="../assets/audio/{slug}_slow.mp3"></audio>'
            f"</span>"
            f'<span class="audio-pair">'
            f'<span class="audio-label">natural</span>'
            f'<audio controls preload="none" '
            f'src="../assets/audio/{slug}_nat.mp3"></audio>'
            f"</span>"
            f"</div>"
        )
    return (
        f'<div class="audio-block" data-slug="{slug}">'
        f'<audio controls preload="none" '
        f'src="../assets/audio/{slug}.mp3"></audio>'
        f"</div>"
    )


def inject_disclaimer(html: str) -> str:
    if 'class="audio-disclaimer"' in html:
        return html
    return html.replace(
        '      </header>\n\n<div class="win"',
        f"      </header>\n{AUDIO_DISCLAIMER}\n\n<div class=\"win\"",
    )


def inject_into_file(html: str, phrase_map: dict) -> str:
    def lookup(text: str):
        info = phrase_map.get(text)
        if info:
            return info["slug"], info["pair"]
        return None

    # 1) Phrase cards: <p class="da">...</p> then <p class="en">
    def _phrase_da(m):
        text = strip_tags(m.group(1))
        info = lookup(text)
        if info is None:
            return m.group(0)
        slug, pair = info
        return f'<p class="da">{m.group(1)}</p>\n        {ablock(slug, pair)}'

    html = re.sub(
        r'<p class="da">(.*?)</p>\s*(?=<p class="en")',
        _phrase_da,
        html,
        flags=re.DOTALL,
    )

    # 2) Dialogue lines: <span class="line">...</span>
    def _line(m):
        text = strip_tags(m.group(1))
        info = lookup(text)
        if info is None:
            return m.group(0)
        slug, pair = info
        return f'<span class="line">{m.group(1)}</span>\n        {ablock(slug, True)}'

    html = re.sub(
        r'<span class="line">(.*?)</span>',
        _line,
        html,
    )

    # 3) Grid cells: <span class="da">...</span>
    def _grid_da(m):
        if "audio-block" in m.group(1):
            return m.group(0)
        text = strip_tags(m.group(1))
        info = lookup(text)
        if info is None:
            return m.group(0)
        slug, pair = info
        return f'<span class="da">{m.group(1)}</span>{ablock(slug, pair)}'

    html = re.sub(
        r'<span class="da">(.*?)</span>(?!\s*<div class="audio-block")',
        _grid_da,
        html,
    )

    # 4) Reference table cells: <td class="da">...</td>
    def _td_da(m):
        if "audio-block" in m.group(1):
            return m.group(0)
        text = strip_tags(m.group(1))
        info = lookup(text)
        if info is None:
            return m.group(0)
        slug, pair = info
        return (
            f'<td class="da">'
            f'{m.group(1)}\n            {ablock(slug, pair)}'
            f"</td>"
        )

    html = re.sub(
        r'<td class="da">(.*?)</td>',
        _td_da,
        html,
        flags=re.DOTALL,
    )

    return html


# ── Main ──────────────────────────────────────────────────────────────


async def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print("Building phrase map...", flush=True)
    phrase_map = build_phrase_map()
    print(f"  {len(phrase_map)} unique texts", flush=True)

    print("Generating audio files...", flush=True)
    await gen_all(phrase_map)

    print("Injecting audio blocks...", flush=True)
    for d in (LESSONS_DIR, REFERENCE_DIR):
        for fp in sorted(d.glob("*.html")):
            html = fp.read_text(encoding="utf-8")
            if "lesson" in fp.name or "000" in fp.name:
                html = inject_disclaimer(html)
            html = inject_into_file(html, phrase_map)
            fp.write_text(html, encoding="utf-8")
            print(f"  {fp.name}", flush=True)

    # Final verification
    print("Verifying...", flush=True)
    audio_files = {f.name for f in AUDIO_DIR.glob("*.mp3") if f.stat().st_size > 0}
    referenced = set()
    for fp in sorted(LESSONS_DIR.glob("*.html")) + sorted(REFERENCE_DIR.glob("*.html")):
        for m in re.finditer(
            r'src="\.\./assets/audio/([^"]+\.mp3)"', fp.read_text()
        ):
            referenced.add(m.group(1))
    missing = referenced - audio_files
    if missing:
        print(f"  WARNING: {len(missing)} missing files!", flush=True)
        for f in sorted(missing):
            print(f"    {f}", flush=True)
    else:
        print(f"  All {len(referenced)} audio references OK", flush=True)

    print("Done.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
