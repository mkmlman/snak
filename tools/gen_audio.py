#!/usr/bin/env python3
"""Prepare lesson/reference HTML for Web Speech API.

Strips audio-block divs and injects speak.js script.
Usage: uv run tools/gen_audio.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISH = ROOT / "docs"
LESSONS_DIR = PUBLISH / "lessons"
REFERENCE_DIR = PUBLISH / "reference"

AUDIO_DISCLAIMER = """\
      <div class="audio-disclaimer" role="note">
        <strong>Audio:</strong> Machine-generated Danish (edge-tts · da-DK-ChristelNeural).
        Helpful for rhythm and recognition — may not perfectly match native Copenhagen pronunciation.
        Prefer what you hear from neighbours when the two differ.
      </div>"""


def strip_audio_blocks(html: str) -> str:
    return re.sub(
        r'<div class="audio-block"[^>]*>.*?</div>\s*',
        "",
        html,
        flags=re.DOTALL,
    )


def strip_toggle(html: str) -> str:
    return re.sub(
        r'\s*<div class="speech-toggle"[^>]*>.*?</div>\s*',
        "",
        html,
        flags=re.DOTALL,
    )


def inject_disclaimer(html: str) -> str:
    if 'class="audio-disclaimer"' in html:
        return html
    return html.replace(
        '      </header>\n\n<div class="win"',
        f"      </header>\n{AUDIO_DISCLAIMER}\n\n<div class=\"win\"",
    )


def inject_script(html: str) -> str:
    html = re.sub(
        r'\s*<script[^>]*src="\.\./assets/speak\.js"[^>]*></script>\s*',
        "",
        html,
    )
    return html.replace(
        "</head>",
        '  <script src="../assets/speak.js" defer></script>\n</head>',
    )


def process_file(fp: Path):
    html = fp.read_text(encoding="utf-8")
    html = strip_audio_blocks(html)
    html = strip_toggle(html)
    html = inject_script(html)
    if "lesson" in fp.name or "000" in fp.name:
        html = inject_disclaimer(html)
    fp.write_text(html, encoding="utf-8")
    print(f"  {fp.name}", flush=True)


def main():
    print("Processing HTML files...", flush=True)
    for d in (LESSONS_DIR, REFERENCE_DIR):
        for fp in sorted(d.glob("*.html")):
            process_file(fp)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
