"""Audio conversion and splitting helpers using ffmpeg."""
import os
import subprocess
import shutil
import math
from . import logger

FFMPEG_BIN = os.environ.get("FFMPEG_PATH", "ffmpeg")

# New generic conversion

def convert_to_mp3(input_path: str, output_path: str):
    """Convert any supported audio file to MP3 (libmp3lame). If already MP3, copy or reuse."""
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

def convert_m4a_to_mp3(m4a_path, mp3_path):
    convert_to_mp3(m4a_path, mp3_path)


def split_mp3(mp3_path, out_pattern, seg_seconds: int):
    logger.info("Splitting %s into %ds segments -> %s", mp3_path, seg_seconds, out_pattern)
    subprocess.check_call([
        FFMPEG_BIN, "-y", "-i", mp3_path,
        "-f", "segment", "-segment_time", str(seg_seconds),
        "-c", "copy", out_pattern
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _get_bitrate_bits(mp3_path: str) -> int | None:
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


def split_mp3_by_size(mp3_path: str, out_pattern: str, max_segment_size: int, fallback_seg_seconds: int):
    """Split an MP3 into segments whose sizes aim to stay below max_segment_size.

    Approach: derive approximate segment duration from bitrate.
    - bitrate bits/sec -> bytes/sec = bitrate/8
    - duration_target = floor((max_segment_size * SAFETY) / bytes_per_sec)
    - Ensure a minimum duration (e.g. 30s) and not more than fallback_seg_seconds.
    If bitrate unknown, fall back to provided seg_seconds.

    If original file already <= max_segment_size -> copy as single seg000.mp3.
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
    logger.info("Splitting %s by size target %d bytes -> estimated duration %ds", mp3_path, max_segment_size, duration_target)
    subprocess.check_call([
        FFMPEG_BIN, "-y", "-i", mp3_path,
        "-f", "segment", "-segment_time", str(duration_target),
        "-c", "copy", out_pattern
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
