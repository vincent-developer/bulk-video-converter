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

# Lower = better quality / larger file.
# Aligned with CompressO Quality slider → libx265/libx264 -crf mapping
# (CompressO uses: CRF = 36 - 12 * quality% / 100, range CRF 24–36):
#
#   CompressO Quality | Label  | CRF
#   ------------------+--------+-----
#    ~1%              | Low    | 36   (smallest files, lowest quality)
#    50% (default)    | Medium | 30   ← current CRF below
#   100%              | High   | 24   (larger files, higher quality)
#
# Recommended CompressO-equivalent range to try here: CRF "24" .. "36"
# (High 100% → Low ~1%). Typical sweet spot: "28"–"32".
CRF = "30"

# Slower presets generally give better compression (e.g. fast, medium, slow)
PRESET = "medium"

# Limit libx265 worker pools (CPU threads for encode).
# 0 = unlimited (FFmpeg/x265 default, often near 100% CPU).
# 2 = good for small CPUs like Intel i3-7100 (2c/4t) so the machine stays usable.
X265_POOLS = 2

# Supported input extensions (case-insensitive)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}
