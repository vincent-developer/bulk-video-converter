# Video Compressor

Batch-compress video files in a single directory using FFmpeg (CPU-only, `libx265` / HEVC).

Works on **macOS**, **Windows**, and **Linux** with the same script. Only install steps and path formats differ.

## Requirements

- Python 3.9+
- FFmpeg with `libx265` and `ffprobe` on `PATH`

## Project files

| File | Purpose |
|---|---|
| [`config.py`](config.py) | **Edit this** — paths, resolution, CRF, preset |
| [`compress_videos.py`](compress_videos.py) | Main script (usually leave as-is) |

Keep both files in the **same folder** so the script can import `config`.

---

## Install by platform

### macOS

1. Install [Homebrew](https://brew.sh/) if needed, then:

```bash
brew install python ffmpeg
```

2. Confirm `libx265` is available:

```bash
ffmpeg -encoders | grep libx265
ffprobe -version
```

3. Edit paths in `config.py` (example):

```python
INPUT_DIR = "/Users/you/Videos/input"
OUTPUT_DIR = "/Users/you/Videos/compressed"
```

4. Run (from the project folder):

```bash
cd /path/to/video-compresser
python3 compress_videos.py
```

**Tip:** Try 1–2 short clips on Mac first to check quality and Apple playback (`hvc1`), then use the same files on a Linux server for the full batch. Encode speed on Mac is not a reliable estimate for server speed.

### Windows

1. Install [Python 3](https://www.python.org/) (enable **Add python.exe to PATH**).
2. Install FFmpeg with `libx265`, e.g.:

```bat
winget install ffmpeg
```

Or use [Chocolatey](https://chocolatey.org/) / a build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/). Restart the terminal after install so `PATH` updates.

3. Confirm:

```bat
ffmpeg -encoders | findstr libx265
ffprobe -version
```

4. Edit paths in `config.py` (raw strings or forward slashes both work):

```python
INPUT_DIR = r"D:\Videos\input"
OUTPUT_DIR = r"D:\Videos\compressed"
# or: INPUT_DIR = "D:/Videos/input"
```

5. Run (from the project folder):

```bat
cd C:\path\to\video-compresser
python compress_videos.py
```

**Notes:** Prefer Windows Terminal or modern PowerShell for cleaner progress updates. Antivirus may slow large encodes slightly.

### Linux (Ubuntu / Debian)

1. Install dependencies:

```bash
sudo apt update
sudo apt install -y python3 ffmpeg
```

2. Confirm:

```bash
ffmpeg -encoders | grep libx265
ffprobe -version
```

3. Edit paths in `config.py` (example):

```python
INPUT_DIR = "/data/videos/input"
OUTPUT_DIR = "/data/videos/compressed"
```

4. Run (from the project folder):

```bash
cd /path/to/video-compresser
python3 compress_videos.py
```

For long batches on a remote server, use `tmux` or `screen` so the job survives disconnects.

---

## Configuration

Open **`config.py`** and edit the settings (do not need to change `compress_videos.py`):

```python
INPUT_DIR = "/path/to/input"       # folder with source videos
OUTPUT_DIR = "/path/to/output"     # compressed files go here (created if missing)
TARGET_RESOLUTION = "original"     # "original" | "1080p" | "720p"
CRF = "30"                         # CompressO Medium 50% equivalent
PRESET = "medium"                  # slower presets = better compression
X265_POOLS = 2                     # limit CPU threads (0 = unlimited)
```

| Setting | Options | Notes |
|---|---|---|
| `TARGET_RESOLUTION` | `original`, `1080p`, `720p` | Never upscales; only downscales when needed |
| `CRF` | typically `24`–`36` | Matches CompressO quality slider (~100%→24, 50%→30, ~1%→36) |
| `PRESET` | e.g. `fast`, `medium`, `slow` | `medium` is the default |
| `X265_POOLS` | `0` or positive int | Caps libx265 CPU pools; `2` suits small CPUs (e.g. i3-7100) |
| `VIDEO_EXTENSIONS` | set of extensions | Default: `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm` |

Supported inputs are top-level files only (no subfolders).

### Example output

```text
Found 3 video(s). Resolution=original, CRF=30, preset=medium
Output directory: /data/videos/compressed
[1/3] Compressing clip.mp4: 45.2%
[1/3] Compressing clip.mp4: 100.0%
  Original: 120.50 MB | Compressed: 42.10 MB | Reduction: 65.1%
[2/3] Skipping already.mp4: output already exists
...
Done. Compressed: 2 | Skipped: 1 | Failed: 0 | Total: 3
```

## Behavior

- Processes videos **one by one** (sequential).
- Writes outputs with the **same filename** (including extension) into `OUTPUT_DIR`.
- **Skips** a file if the output path already exists.
- Preserves media metadata (`-map_metadata 0`) and OS timestamps (`shutil.copystat`).
- Uses Apple-compatible tagging (`-tag:v hvc1`).
- On FFmpeg failure for one file, removes any partial output and continues with the next.

## Moving between Mac / Windows / Linux

No code changes are required. When you deploy or switch machines:

1. Install Python + FFmpeg with `libx265` on that OS.
2. Update `INPUT_DIR` and `OUTPUT_DIR` in **`config.py`** for that machine.
3. Keep `config.py` next to `compress_videos.py`, then run the same script.

Keep originals until you have verified a few compressed samples.
