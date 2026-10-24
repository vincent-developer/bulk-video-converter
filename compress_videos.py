#!/usr/bin/env python3
"""Batch-compress video files in a directory using FFmpeg (CPU / libx265)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from config import (
    CRF,
    INPUT_DIR,
    OUTPUT_DIR,
    PRESET,
    TARGET_RESOLUTION,
    VIDEO_EXTENSIONS,
    X265_POOLS,
)

SCALE_FILTERS = {
    "original": None,
    "1080p": "scale='min(iw,1920):-2'",
    "720p": "scale='min(iw,1280):-2'",
}

TIME_RE = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d+)")


def format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def check_tools() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            print(f"Error: '{tool}' not found on PATH. Install FFmpeg and retry.", file=sys.stderr)
            sys.exit(1)


def list_videos(input_dir: Path) -> list[Path]:
    videos: list[Path] = []
    for entry in sorted(input_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(entry)
    return videos


def get_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    value = result.stdout.strip()
    if not value or value == "N/A":
        raise RuntimeError("could not determine video duration")
    duration = float(value)
    if duration <= 0:
        raise RuntimeError(f"invalid duration: {duration}")
    return duration


def parse_time_to_seconds(match: re.Match[str]) -> float:
    hours, minutes, seconds, frac = match.groups()
    frac_seconds = float(f"0.{frac}")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + frac_seconds


def build_ffmpeg_cmd(input_path: Path, output_path: Path) -> list[str]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(input_path),
        "-map_metadata",
        "0",
        "-c:v",
        "libx265",
        "-crf",
        CRF,
        "-preset",
        PRESET,
        "-tag:v",
        "hvc1",
    ]
    if X265_POOLS and X265_POOLS > 0:
        cmd.extend(["-x265-params", f"pools={int(X265_POOLS)}"])
    scale = SCALE_FILTERS[TARGET_RESOLUTION]
    if scale:
        cmd.extend(["-vf", scale])
    cmd.extend(
        [
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-n",
            str(output_path),
        ]
    )
    return cmd


def compress_one(
    input_path: Path,
    output_path: Path,
    index: int,
    total: int,
) -> bool:
    label = f"[{index}/{total}] Compressing {input_path.name}"
    try:
        duration = get_duration(input_path)
    except Exception as exc:
        print(f"{label}: failed to probe duration ({exc})", file=sys.stderr)
        return False

    cmd = build_ffmpeg_cmd(input_path, output_path)
    try:
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        print(f"\n{label}: failed to start ffmpeg ({exc})", file=sys.stderr)
        return False

    assert process.stderr is not None
    last_pct = -1.0

    def update_progress(chunk: str) -> None:
        nonlocal last_pct
        match = TIME_RE.search(chunk)
        if not match or duration <= 0:
            return
        elapsed = parse_time_to_seconds(match)
        pct = min(100.0, (elapsed / duration) * 100.0)
        if abs(pct - last_pct) >= 0.05 or pct >= 100.0:
            print(f"\r{label}: {pct:.1f}%", end="", flush=True)
            last_pct = pct

    try:
        # FFmpeg progress updates often use '\r' instead of newlines.
        buffer = ""
        while True:
            piece = process.stderr.read(256)
            if not piece:
                break
            buffer += piece
            while True:
                sep_r = buffer.find("\r")
                sep_n = buffer.find("\n")
                if sep_r == -1 and sep_n == -1:
                    break
                if sep_r == -1:
                    sep = sep_n
                elif sep_n == -1:
                    sep = sep_r
                else:
                    sep = min(sep_r, sep_n)
                update_progress(buffer[:sep])
                buffer = buffer[sep + 1 :]
        if buffer:
            update_progress(buffer)
        returncode = process.wait()
    except Exception as exc:
        process.kill()
        process.wait()
        print(f"\n{label}: error while encoding ({exc})", file=sys.stderr)
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        return False

    if returncode != 0:
        print(f"\n{label}: ffmpeg failed (exit {returncode})", file=sys.stderr)
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        return False

    print(f"\r{label}: 100.0%")
    shutil.copystat(input_path, output_path)

    original_size = input_path.stat().st_size
    compressed_size = output_path.stat().st_size
    if original_size > 0:
        reduction = (1.0 - (compressed_size / original_size)) * 100.0
    else:
        reduction = 0.0

    print(
        f"  Original: {format_size(original_size)} | "
        f"Compressed: {format_size(compressed_size)} | "
        f"Reduction: {reduction:.1f}%"
    )
    return True


def main() -> None:
    if TARGET_RESOLUTION not in SCALE_FILTERS:
        print(
            f"Error: invalid TARGET_RESOLUTION '{TARGET_RESOLUTION}'. "
            f"Use one of: {', '.join(SCALE_FILTERS)}",
            file=sys.stderr,
        )
        sys.exit(1)

    check_tools()

    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)

    if not input_dir.is_dir():
        print(f"Error: INPUT_DIR does not exist or is not a directory: {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    videos = list_videos(input_dir)
    if not videos:
        print(f"No supported video files found in {input_dir}")
        sys.exit(0)

    total = len(videos)
    compressed = 0
    skipped = 0
    failed = 0

    print(f"Found {total} video(s). Resolution={TARGET_RESOLUTION}, CRF={CRF}, preset={PRESET}")
    print(f"Output directory: {output_dir}")

    for index, video in enumerate(videos, start=1):
        output_path = output_dir / video.name
        if output_path.exists():
            print(f"[{index}/{total}] Skipping {video.name}: output already exists")
            skipped += 1
            continue

        if compress_one(video, output_path, index, total):
            compressed += 1
        else:
            failed += 1

    print(
        f"\nDone. Compressed: {compressed} | Skipped: {skipped} | Failed: {failed} | Total: {total}"
    )


if __name__ == "__main__":
    main()
