# Video Compressor

Batch-compress video files in a single directory using FFmpeg — either **CPU** (`libx265`) or **NVIDIA GPU** (`hevc_nvenc`).

Works on **macOS**, **Windows**, and **Linux** with the same script. Only install steps, paths, and the `USE_GPU` toggle differ.

## Requirements

- Python 3.9+
- FFmpeg with `ffprobe` on `PATH`
- **CPU mode:** FFmpeg with `libx265`
- **GPU mode:** NVIDIA GPU + drivers + FFmpeg built with `hevc_nvenc`

## Project files

| File | Purpose |
|---|---|
| [`config.py`](config.py) | **Edit this** — paths, `USE_GPU`, CRF/CQ, preset, pools |
| [`compress_videos.py`](compress_videos.py) | Main script (usually leave as-is) |

Keep both files in the **same folder** so the script can import `config`.

---

## Hardware: Axioo Pongo 960

Primary GPU workflow target:

- **CPU:** Intel Core i9 (13th Gen)
- **GPU:** NVIDIA GeForce RTX 4060
- **RAM:** 32GB

On this laptop, set `USE_GPU = True` in `config.py` to encode with the RTX 4060 **NVENC** hardware encoder (`hevc_nvenc`). Batches are typically **much faster** than CPU-only `libx265`. Expect laptop fans to run hard (often near max) under sustained NVENC + decode load — that is normal thermal behavior, not a script bug.

Confirm NVENC is available:

```bat
ffmpeg -encoders | findstr hevc_nvenc
```

```bash
ffmpeg -encoders | grep hevc_nvenc
```

### Non-NVIDIA machines

`hevc_nvenc` is **NVIDIA-only**. Set `USE_GPU = False` on:

- Apple Silicon Macs (M1–M4) — use CPU `libx265`
- AMD Radeon systems
- CPU-only PCs (e.g. Intel i3-7100 with no NVIDIA GPU)

If `USE_GPU = True` and NVENC is missing/fails, that file **fails** and the batch continues — there is **no** automatic CPU fallback.

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

3. In `config.py`, set `USE_GPU = False` (no NVENC on Mac).

4. Run (from the project folder):

```bash
cd /path/to/video-compresser
python3 compress_videos.py
```

**Tip:** Try 1–2 short clips on Mac first to check quality and Apple playback (`hvc1`). Encode speed on Mac is not a reliable estimate for the Pongo RTX 4060.

### Windows (including Axioo Pongo 960)

1. Install [Python 3](https://www.python.org/) (enable **Add python.exe to PATH**).
2. Install FFmpeg with `libx265` and (for GPU) `hevc_nvenc`, e.g.:

```bat
winget install ffmpeg
```

Or use [Chocolatey](https://chocolatey.org/) / a build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/). Restart the terminal after install so `PATH` updates. Install/update **NVIDIA drivers** for the RTX 4060.

3. Confirm:

```bat
ffmpeg -encoders | findstr libx265
ffmpeg -encoders | findstr hevc_nvenc
ffprobe -version
```

4. In `config.py`, set `USE_GPU = True` on the Pongo (RTX 4060), or `False` if you want CPU-only.

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

For NVENC on Linux you typically need a non-default FFmpeg build with NVENC plus proprietary NVIDIA drivers — confirm with `ffmpeg -encoders | grep hevc_nvenc`.

2. Confirm CPU encoder at minimum:

```bash
ffmpeg -encoders | grep libx265
ffprobe -version
```

3. Set `USE_GPU` in `config.py` only if NVENC works on that host.

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
USE_GPU = True                     # True = hevc_nvenc (NVIDIA); False = libx265 (CPU)
TARGET_RESOLUTION = "original"     # "original" | "1080p" | "720p"
CRF = "30"                         # CPU: -crf; GPU: -cq (same number)
PRESET = "medium"                  # CPU only
X265_POOLS = 2                     # CPU only (0 = unlimited)
```

| Setting | Options | Notes |
|---|---|---|
| `USE_GPU` | `True` / `False` | NVIDIA NVENC vs CPU libx265 |
| `TARGET_RESOLUTION` | `original`, `1080p`, `720p` | Never upscales; only downscales when needed |
| `CRF` | typically `24`–`36` | CompressO-style scale (~100%→24, 50%→30, ~1%→36). Used as `-crf` (CPU) or `-cq` (GPU) |
| `PRESET` | e.g. `fast`, `medium`, `slow` | CPU only; GPU uses fixed NVENC `p6` + `tune hq` |
| `X265_POOLS` | `0` or positive int | CPU only; caps libx265 pools (e.g. `2` on i3-7100) |
| `VIDEO_EXTENSIONS` | set of extensions | Default: `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm` |

Supported inputs are top-level files only (no subfolders). Default folders are project-local `input/` and `output/`.

### Example output

```text
Found 3 video(s). Resolution=original
Encoder: hevc_nvenc (GPU), cq=30, preset=p6, tune=hq
Output directory: .../output
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
- On FFmpeg failure for one file, removes any partial output and continues with the next (including NVENC errors when `USE_GPU = True`).

## Moving between Mac / Windows / Linux

1. Install Python + FFmpeg (`libx265`; add NVENC only where needed).
2. Set `USE_GPU` appropriately for that machine’s GPU.
3. Keep `config.py` next to `compress_videos.py`, then run the same script.

Keep originals until you have verified a few compressed samples.
