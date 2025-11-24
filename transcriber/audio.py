"""Audio conversion and splitting helpers using ffmpeg."""
from __future__ import annotations
import os
import subprocess
import shutil
from typing import Optional
from . import logger
from .constants import ENV_FFMPEG_PATH, DEFAULT_FFMPEG_PATH

FFMPEG_BIN: str = os.environ.get(ENV_FFMPEG_PATH, DEFAULT_FFMPEG_PATH)


def convert_to_mp3(input_path: str, output_path: str) -> None:
    """Convert any supported audio file to MP3 (libmp3lame).

    If the input is already an MP3, copy to the target path (if different).
    """
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".mp3":
        # If output different path, just copy
        if input_path != output_path:
            shutil.copyfile(input_path, output_path)
            logger.debug("Copied MP3 %s -> %s", input_path, output_path)
        else:
            logger.debug("Input already MP3 and same path: %s", input_path)
        return
    logger.info("Converting %s to mp3 -> %s", input_path, output_path)
    subprocess.check_call([
        FFMPEG_BIN, "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Backwards compatibility wrapper

def convert_m4a_to_mp3(m4a_path: str, mp3_path: str) -> None:
    convert_to_mp3(m4a_path, mp3_path)


def split_mp3(mp3_path: str, out_pattern: str, seg_seconds: int) -> None:
    """Split an MP3 into fixed-length segments using stream copy (no re-encode)."""
    logger.info("Splitting %s into %ds segments -> %s", mp3_path, seg_seconds, out_pattern)
    subprocess.check_call([
        FFMPEG_BIN, "-y", "-i", mp3_path,
        "-f", "segment", "-segment_time", str(seg_seconds),
        "-c", "copy", out_pattern
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _get_bitrate_bits(mp3_path: str) -> Optional[int]:
    """Return overall bitrate in bits/sec for an mp3 file using ffprobe, or None if unavailable."""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ], stderr=subprocess.DEVNULL).decode().strip()
        return int(out)
    except Exception:
        logger.debug("Could not determine bitrate for %s", mp3_path)
        return None


def split_mp3_by_size(mp3_path: str, out_pattern: str, max_segment_size: int, fallback_seg_seconds: int) -> None:
    """Split an MP3 into segments sized under a target byte ceiling.

    Approach: derive approximate segment duration from bitrate.
    If bitrate is unknown, fall back to provided seg_seconds.

    If the original file is already <= max_segment_size, emit a single seg000.mp3.
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(mp3_path)
    raw_size = os.path.getsize(mp3_path)
    if raw_size <= max_segment_size:
        single_out = out_pattern.replace("%03d", "000")
        shutil.copyfile(mp3_path, single_out)
        logger.debug("File %s already <= max_segment_size (%d bytes); copied to %s", mp3_path, raw_size, single_out)
        return
    bitrate_bits = _get_bitrate_bits(mp3_path)
    SAFETY = 0.9
    if bitrate_bits and bitrate_bits > 0:
        bytes_per_sec = bitrate_bits / 8.0
        duration_target = int((max_segment_size * SAFETY) / bytes_per_sec)
        # Clamp
        duration_target = max(30, duration_target)
        duration_target = min(fallback_seg_seconds, duration_target)
    else:
        duration_target = fallback_seg_seconds
        logger.debug("Falling back to seg_seconds=%s for %s", fallback_seg_seconds, mp3_path)
    logger.info(
        "Splitting %s by size target %d bytes -> estimated duration %ds",
        mp3_path,
        max_segment_size,
        duration_target,
    )
    subprocess.check_call([
        FFMPEG_BIN, "-y", "-i", mp3_path,
        "-f", "segment", "-segment_time", str(duration_target),
        "-c", "copy", out_pattern
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
