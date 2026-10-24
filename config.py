"""User configuration for compress_videos.py — edit this file before running."""

from pathlib import Path

# Project root (folder that contains this config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent

# Folder with source videos (top-level files only; subfolders are ignored)
INPUT_DIR = str(_PROJECT_ROOT / "input")

# Compressed files are written here (created automatically if missing)
OUTPUT_DIR = str(_PROJECT_ROOT / "output")

# "original" | "1080p" | "720p" — never upscales; only downscales when needed
TARGET_RESOLUTION = "original"

# True = NVIDIA NVENC (hevc_nvenc). False = CPU libx265.
# Only works with an NVIDIA GPU + FFmpeg built with NVENC (e.g. Axioo Pongo 960 RTX 4060).
# Set False on Mac (Apple Silicon), AMD Radeon, or CPU-only machines (e.g. i3-7100).
# On NVENC failure there is no automatic CPU fallback — that file fails and the batch continues.
USE_GPU = False

# Lower = better quality / larger file.
# CPU path (USE_GPU=False): passed as libx265 -crf
# GPU path (USE_GPU=True):  passed as hevc_nvenc -cq (same numeric value)
#
# Aligned with CompressO Quality slider → CRF mapping
# (CompressO uses: CRF = 36 - 12 * quality% / 100, range CRF 24–36):
#
#   CompressO Quality | Label  | CRF / CQ
#   ------------------+--------+---------
#    ~1%              | Low    | 36   (smallest files, lowest quality)
#    50% (default)    | Medium | 30   ← current value below
#   100%              | High   | 24   (larger files, higher quality)
#
# Recommended CompressO-equivalent range: "24" .. "36". Typical sweet spot: "28"–"32".
CRF = "30"

# CPU only (libx265). Slower presets generally give better compression (e.g. fast, medium, slow).
# Ignored when USE_GPU is True (GPU uses NVENC preset p6 + tune hq).
PRESET = "medium"

# CPU only: limit libx265 worker pools (encode threads).
# 0 = unlimited (FFmpeg/x265 default, often near 100% CPU).
# 2 = good for small CPUs like Intel i3-7100 (2c/4t) so the machine stays usable.
# Ignored when USE_GPU is True.
X265_POOLS = 0

# Supported input extensions (case-insensitive)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}
