#!/usr/bin/env python3
"""Prepare three short, gentle nature cues from public-domain field recordings.

Source files and authors are documented in AUDIO-SOURCES.md.
Generated MP3 clips are kept in the application for deterministic offline playback.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import subprocess
import json
import wave
import math

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "meditation" / "sounds"
DEST.mkdir(parents=True, exist_ok=True)

CLIPS = (
    {
        "name": "foret",
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/38/Birds_forest.ogg",
        "start": 5.5,
        "duration": 1.18,
        "lowpass": 3000,
    },
    {
        "name": "oiseau",
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Gentle_breeze_and_birds_singing.ogg",
        "start": 10.6,
        "duration": 1.02,
        "lowpass": 2900,
    },
    {
        "name": "sousbois",
        "url": "https://upload.wikimedia.org/wikipedia/commons/b/b4/Walk_in_the_rainforest.ogg",
        "start": 5.8,
        "duration": 1.22,
        "lowpass": 2600,
    },
)

for clip in CLIPS:
    original = DEST / (clip["name"] + "-source.ogg")
    req = Request(clip["url"], headers={"User-Agent": "silence-meditation-project/1.0"})
    with urlopen(req, timeout=35) as response:
        original.write_bytes(response.read())
    if not original.read_bytes().startswith(b"OggS"):
        raise RuntimeError("Source file was not OGG: " + clip["name"])
    output = DEST / (clip["name"] + ".mp3")
    duration = clip["duration"]
    # A natural texture, without sharp attack or ringing synthetic notes.
    # Two soft fades prevent any abrupt onset or cutoff.
    filters = (
        "highpass=f=145,"
        f"lowpass=f={clip['lowpass']},"
        "acompressor=threshold=-24dB:ratio=1.3:attack=35:release=280,"
        "afade=t=in:st=0:d=0.23,"
        f"afade=t=out:st={duration - 0.39:.2f}:d=0.39,"
        "loudnorm=I=-23:TP=-10:LRA=7"
    )
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(clip["start"]), "-i", str(original),
        "-t", str(duration),
        "-ac", "1", "-ar", "24000",
        "-af", filters,
        "-codec:a", "libmp3lame", "-b:a", "64k",
        str(output),
    ], check=True)
    probe = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "json", str(output)
    ])
    seconds = float(json.loads(probe)["format"]["duration"])
    if seconds < 0.8 or seconds > 1.4 or output.stat().st_size < 1200:
        raise RuntimeError(f"Invalid audio {clip['name']} {seconds}s")
    print(f"{clip['name']}: {seconds:.2f} sec, {output.stat().st_size} bytes")
    original.unlink()

print("Three nature cues ready.")
