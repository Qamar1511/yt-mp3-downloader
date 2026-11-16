# YouTube to MP3 Downloader (Desktop App)

A simple desktop app (Python + tkinter) that converts a YouTube video or a whole
playlist into MP3 files using [yt-dlp](https://github.com/yt-dlp/yt-dlp) and ffmpeg.

## Features
- Single video or full playlist (parallel downloads, you choose how many)
- Quality choice: 128 / 192 / 256 / 320 kbps
- Skips MP3 files that already exist, so you can resume a playlist
- Progress bar, Stop button, and error log (`errors.txt`)

## Requirements
- Python 3.9+
- ffmpeg
- yt-dlp

## Setup
```
pip install -U yt-dlp
winget install ffmpeg        # Windows (Mac: brew install ffmpeg)
python yt_mp3_downloader.py
```
Keep yt-dlp updated (`pip install -U yt-dlp`), old versions get slow or blocked.

## Build a Windows .exe
Double-click `build_exe.bat`. The exe appears in `dist/`.
Put `ffmpeg.exe` next to the exe, or install ffmpeg on the system.

## Tips
- Use real playlist links (`youtube.com/playlist?list=PL...`), not auto-generated Mix links (`list=RD...`).
- If you see `HTTP 429 Too Many Requests`, lower "parallel downloads" and wait a while.

## Disclaimer
This tool is for personal use with content you have the right to download
(your own uploads, Creative Commons, public domain, or where the creator allows it).
Downloading copyrighted content may violate YouTube's Terms of Service and copyright law.
You are responsible for how you use it.
