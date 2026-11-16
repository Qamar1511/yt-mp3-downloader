"""
YouTube -> MP3 Downloader v3 (fast: parallel playlist download)

Setup (ek baar):
    pip install -U yt-dlp
    ffmpeg install karo:  winget install ffmpeg   (Mac: brew install ffmpeg)

Chalane ke liye:
    python yt_mp3_downloader.py

Note: Sirf wahi content download karo jiska aapke paas haq ho
(apna video, Creative Commons, ya jahan creator ne permission di ho).
"""

import os
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, filedialog, messagebox

import yt_dlp
from yt_dlp.utils import sanitize_filename

# .exe ya script ke saath rakha ffmpeg.exe bhi mil jaye
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                           else os.path.abspath(__file__))
os.environ["PATH"] = BASE_DIR + os.pathsep + os.environ.get("PATH", "")


def clean(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "playlist"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube to MP3 (Fast, Playlist support)")
        self.geometry("560x340")
        self.resizable(False, False)

        self.save_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.quality = tk.StringVar(value="192")
        self.workers = tk.StringVar(value="3")
        self.status = tk.StringVar(value="Video ya playlist ka link paste karo")
        self.stop_flag = False
        self.lock = threading.Lock()

        pad = {"padx": 14, "pady": 5}

        ttk.Label(self, text="YouTube video / playlist link:").pack(anchor="w", **pad)
        self.url_entry = ttk.Entry(self, width=75)
        self.url_entry.pack(**pad)

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Save folder:").pack(side="left")
        ttk.Entry(row, textvariable=self.save_dir, width=42).pack(side="left", padx=6)
        ttk.Button(row, text="Browse", command=self.choose_dir).pack(side="left")

        row2 = ttk.Frame(self)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="Quality (kbps):").pack(side="left")
        ttk.Combobox(row2, textvariable=self.quality, values=["128", "192", "256", "320"],
                     width=5, state="readonly").pack(side="left", padx=6)
        ttk.Label(row2, text="Ek saath kitne:").pack(side="left", padx=(14, 0))
        ttk.Combobox(row2, textvariable=self.workers, values=["1", "2", "3", "4", "5"],
                     width=3, state="readonly").pack(side="left", padx=6)

        btns = ttk.Frame(self)
        btns.pack(pady=8)
        self.btn = ttk.Button(btns, text="Download MP3", command=self.start)
        self.btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        ttk.Label(self, text="Overall progress:").pack(anchor="w", padx=14)
        self.total_bar = ttk.Progressbar(self, length=520, mode="determinate")
        self.total_bar.pack(**pad)

        ttk.Label(self, textvariable=self.status, wraplength=520).pack(**pad)

    # ---------- UI helpers ----------
    def ui(self, fn):
        self.after(0, fn)

    def set_status(self, text):
        self.ui(lambda: self.status.set(text))

    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir.get())
        if d:
            self.save_dir.set(d)

    def confirm(self, text):
        result = {}
        done = threading.Event()

        def ask():
            result["v"] = messagebox.askyesno("Confirm", text)
            done.set()

        self.after(0, ask)
        done.wait()
        return result["v"]

    def stop(self):
        self.stop_flag = True
        self.set_status("Rok rahe hain... chal rahe videos khatam hone ke baad ruk jayega")

    def start(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Link missing", "Pehle YouTube link daalo.")
            return
        self.stop_flag = False
        self.btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.total_bar["value"] = 0
        self.set_status("Link check ho raha hai...")
        threading.Thread(target=self.run, args=(url,), daemon=True).start()

    # ---------- Download logic ----------
    def make_opts(self, outdir, n_workers):
        return {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": os.path.join(outdir, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "concurrent_fragment_downloads": 4 if n_workers > 1 else 8,
            "http_chunk_size": 10 * 1024 * 1024,
            "retries": 5,
            "fragment_retries": 5,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": self.quality.get(),
            }],
        }

    def run(self, url):
        try:
            if not shutil.which("ffmpeg"):
                self.set_status("ERROR: ffmpeg install nahi hai. cmd mein 'winget install ffmpeg' "
                                "chalao, phir cmd band karke dobara kholo.")
                return

            # 1) list nikalo (fast)
            with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": "in_playlist",
                                   "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)

            if info.get("entries"):
                entries = [e for e in info["entries"] if e]
                outdir = os.path.join(self.save_dir.get(), clean(info.get("title", "playlist")))
                items = []
                for e in entries:
                    vid = e.get("url") or e.get("id")
                    if vid and not vid.startswith("http"):
                        vid = f"https://www.youtube.com/watch?v={vid}"
                    items.append((e.get("title") or vid, vid))
            else:
                outdir = self.save_dir.get()
                items = [(info.get("title", url), url)]

            total = len(items)
            if total > 1:
                warn = ""
                if "list=RD" in url:
                    warn = ("\n\nDhyan do: ye YouTube ka Mix/Radio link hai, "
                            "aapki asli playlist nahi.")
                if not self.confirm(f"Is link mein {total} videos mile.{warn}\n\nSabhi download karein?"):
                    self.set_status("Cancel kar diya. Sahi playlist ka link daalo.")
                    return

            os.makedirs(outdir, exist_ok=True)

            # jo MP3 folder mein pehle se hain unhe skip karo
            existing = {os.path.splitext(f)[0].lower()
                        for f in os.listdir(outdir) if f.lower().endswith(".mp3")}
            todo = [it for it in items
                    if sanitize_filename(it[0] or "").lower() not in existing]
            skipped = total - len(todo)

            if not todo:
                self.set_status(f"Sab {total} gaane pehle se downloaded hain.\nFolder: {outdir}")
                return

            n_workers = max(1, min(int(self.workers.get()), len(todo)))
            state = {"done": skipped, "failed": 0, "last_error": ""}
            self.ui(lambda v=skipped / total * 100: self.total_bar.configure(value=v))

            # 2) parallel download
            def work(item):
                if self.stop_flag:
                    return
                title, link = item
                try:
                    with yt_dlp.YoutubeDL(self.make_opts(outdir, n_workers)) as ydl:
                        ydl.download([link])
                except Exception as e:
                    with self.lock:
                        state["failed"] += 1
                        state["last_error"] = str(e)
                        with open(os.path.join(outdir, "errors.txt"), "a", encoding="utf-8") as f:
                            f.write(f"{title}\n  {e}\n\n")
                finally:
                    with self.lock:
                        state["done"] += 1
                        d = state["done"]
                    self.ui(lambda v=d / total * 100: self.total_bar.configure(value=v))
                    self.set_status(f"{d}/{total} complete  (fail: {state['failed']})")

            self.set_status(f"{skipped} pehle se hain (skip). Baaki {len(todo)} download ho rahe hain "
                            f"- {n_workers} ek saath...")
            with ThreadPoolExecutor(max_workers=n_workers) as pool:
                list(pool.map(work, todo))

            ok = total - state["failed"]
            msg = "Stop kar diya." if self.stop_flag else f"Ho gaya! {ok}/{total} downloaded."
            if state["failed"]:
                msg += f" Fail hue: {state['failed']}. Last error: {state['last_error'][:250]}"
            self.set_status(msg + f"\nFolder: {outdir}")

            if ok > 0:
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(outdir)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", outdir])
                except Exception:
                    pass
        except Exception as e:
            self.set_status(f"Error: {e}")
        finally:
            self.ui(lambda: self.btn.config(state="normal"))
            self.ui(lambda: self.stop_btn.config(state="disabled"))


if __name__ == "__main__":
    App().mainloop()
