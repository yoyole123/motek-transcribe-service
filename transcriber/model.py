"""Model loading + transcription logic."""
from __future__ import annotations
import os
import re
import asyncio
import subprocess
from typing import List, Dict, Any, Tuple
from .utils import clean_some_unicode_from_text

def _format_ts(seconds: float) -> str:
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _probe_duration(path: str) -> float:
    """Return duration in seconds using ffprobe; fallback to 0 on error."""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path
        ], stderr=subprocess.DEVNULL).decode().strip()
        return float(out)
    except Exception:
        return 0.0


async def transcribe_segment(model, segment_path: str, index: int, start_s: float, end_s: float, max_retries: int):
    attempts = max_retries + 1  # total attempts including first
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        try:
            print(f"Transcribing segment {index} attempt {attempt}/{attempts}: {segment_path}")
            segs = model.transcribe_async(path=segment_path, diarize=True)
            collected: List[str] = []
            async for s in segs:
                collected.append(clean_some_unicode_from_text(s.text))
            text = "\n".join(collected).strip()
            if text:
                print(f"Finished segment {index} attempt {attempt}")
                return {"index": index, "text": text}
            else:
                last_error = "empty transcription"
                print(f"Empty result for segment {index} attempt {attempt}")
        except Exception as e:
            last_error = str(e)
            print(f"Error transcribing segment {index} attempt {attempt}: {e}")
        # Retry if more attempts left
        if attempt < attempts:
            # simple linear backoff
            await asyncio.sleep(attempt)
    # All attempts failed -> build placeholder
    start_ts = _format_ts(start_s)
    end_ts = _format_ts(end_s)
    reason = last_error or "unknown"
    placeholder = f"[Transcription failed - {start_ts} - {end_ts} Reason: {reason}]"
    return {"index": index, "text": placeholder}


async def transcribe_file(model, mp3_full_path: str, work_dir: str, seg_seconds: int, max_concurrency: int, bypass_split: bool, splitter_fn, max_segment_retries: int):
    out_pattern = os.path.join(work_dir, "seg%03d.mp3")
    if bypass_split:
        segments = sorted([f for f in os.listdir(work_dir) if re.match(r"seg\d{3}\.mp3", f)])
    else:
        splitter_fn(mp3_full_path, out_pattern, seg_seconds)
        segments = sorted([f for f in os.listdir(work_dir) if re.match(r"seg\d{3}\.mp3", f)])
    if not segments:
        return "", []
    # Compute start/end times based on actual segment durations (fallback to seg_seconds if unknown)
    durations: List[float] = []
    for fname in segments:
        path = os.path.join(work_dir, fname)
        d = _probe_duration(path) or float(seg_seconds)
        durations.append(d)
    starts: List[float] = []
    ends: List[float] = []
    cursor = 0.0
    for d in durations:
        starts.append(cursor)
        cursor += d
        ends.append(cursor)
    sem = asyncio.Semaphore(max_concurrency)

    async def run_segment(idx: int, fname: str):
        seg_path = os.path.join(work_dir, fname)
        async with sem:
            return await transcribe_segment(model, seg_path, idx, starts[idx], ends[idx], max_segment_retries)

    tasks = [asyncio.create_task(run_segment(idx, fname)) for idx, fname in enumerate(segments)]
    results = await asyncio.gather(*tasks)
    ordered = sorted(results, key=lambda r: r["index"])
    full_text = "\n\n".join(r["text"] for r in ordered)
    return full_text, segments


def load_model(runpod_api_key: str | None, runpod_endpoint_id: str | None, languages_cfg: Dict[str, Any], language: str = "he"):
    if not runpod_api_key or not runpod_endpoint_id:
        raise RuntimeError("RUNPOD_API_KEY or RUNPOD_ENDPOINT_ID not set.")
    import ivrit  # Lazy import
    lang_cfg = languages_cfg.get(language)
    if not lang_cfg:
        raise RuntimeError(f"Language '{language}' not found in config.")
    model_name = lang_cfg.get("model")
    if not model_name:
        raise RuntimeError(f"Model not configured for language '{language}'.")
    print(f"Loading model '{model_name}' for language '{language}' via RunPod endpoint {runpod_endpoint_id}...")
    return ivrit.load_model(engine='runpod', model=model_name, api_key=runpod_api_key, endpoint_id=runpod_endpoint_id, core_engine='stable-whisper')
