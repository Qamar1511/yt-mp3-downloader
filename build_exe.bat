@echo off
REM Windows par .exe banane ke liye is file par double-click karo
pip install -U yt-dlp pyinstaller
pyinstaller --onefile --windowed --collect-all yt_dlp --name YT-MP3-Downloader yt_mp3_downloader.py
echo.
echo Done! Exe yahan hai: dist\YT-MP3-Downloader.exe
echo ffmpeg.exe ko usi exe ke saath rakhna (ya ffmpeg system mein install ho).
pause
