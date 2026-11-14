#!/usr/bin/env python3
"""Produce one unobtrusive, isolated bird chirp for silence.

Source: public-domain Birds forest.ogg, credit in AUDIO-SOURCES.md.
This is a time cue, not background ambience.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import audioop
import json
import re
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "meditation" / "sounds"
DEST.mkdir(parents=True, exist_ok=True)
SOURCE = "https://upload.wikimedia.org/wikipedia/commons/3/38/Birds_forest.ogg"
raw = DEST / "_bird_source.ogg"
with urlopen(Request(SOURCE, headers={"User-Agent": "silence-meditation-project/1.0"}), timeout=40) as response:
    raw.write_bytes(response.read())
if not raw.read_bytes().startswith(b"OggS"):
    raise RuntimeError("Unexpected source encoding")

# Detect a short foreground bird call rather than extracting sustained forest ambience.
pcm = subprocess.check_output([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(raw),
    "-t", "24", "-af", "highpass=f=1300,lowpass=f=3400",
    "-ac", "1", "-ar", "16000", "-f", "s16le", "pipe:1"
])
rate = 16000
chunk = rate // 50  # 20 ms
levels = [audioop.rms(pcm[i:i + chunk * 2], 2)
          for i in range(0, len(pcm) - chunk * 2, chunk * 2)]
if len(levels) < 160:
    raise RuntimeError("Not enough field recording for an isolated chirp")
noise = max(1.0, statistics.median(levels))
choices = []
for i in range(110, len(levels) - 35):
    middle = statistics.mean(levels[i:i + 11])
    before = statistics.mean(levels[i - 13:i - 3])
    after = statistics.mean(levels[i + 14:i + 24])
    contrast = middle / max(1.0, (before + after) / 2)
    # Seek a short bird-like event (above background) with quieter surroundings.
    if middle > noise * 1.45:
        score = middle * min(2.8, contrast) ** 2
        choices.append((score, i))
if not choices:
    raise RuntimeError("No identifiable short bird signal in the source")
_, chosen = max(choices)
start = max(0, chosen * .02 - .075)
duration = .34
output = DEST / "pepiement.mp3"
filters = (
    "highpass=f=1300,lowpass=f=3400,"
    "afade=t=in:st=0:d=0.065,"
    "afade=t=out:st=0.17:d=0.17,"
    "loudnorm=I=-26:TP=-9:LRA=4,"
    "volume=-5dB"
)
subprocess.run([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-ss", f"{start:.3f}", "-i", str(raw),
    "-t", str(duration), "-ac", "1", "-ar", "24000",
    "-af", filters, "-codec:a", "libmp3lame", "-b:a", "64k", str(output)
], check=True)
probe = json.loads(subprocess.check_output([
    "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
    "-of", "json", str(output)
]))
seconds = float(probe["format"]["duration"])
if not .32 <= seconds <= .46 or not 1500 <= output.stat().st_size <= 7000:
    raise RuntimeError(f"Unexpected duration or bytes: {seconds:.3f}s")
volume = subprocess.run([
    "ffmpeg", "-i", str(output), "-af", "volumedetect", "-f", "null", "-"
], text=True, capture_output=True, check=True)
match = re.search(r"max_volume:\\s*(-?[0-9.]+) dB", volume.stderr)
if not match or float(match.group(1)) > -12:
    raise RuntimeError("Chirp is too loud: " + (match.group(1) if match else "unknown"))
print(f"Isolated natural chirp at {start:.2f}s: {seconds:.2f}s; peak {match.group(1)} dBFS; {output.stat().st_size} bytes")
raw.unlink()
