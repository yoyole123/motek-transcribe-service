import re
import asyncio
import os
import pytest
from transcriber.model import transcribe_file

class DummyModel:
    def transcribe_async(self, path, diarize=True):
        async def gen():
            raise Exception("boom")
            yield  # unreachable
        return gen()


def test_failed_segments_placeholder(tmp_path):
    # Create two dummy segment files that will be picked up (empty mp3 files)
    seg0 = tmp_path / "seg000.mp3"
    seg1 = tmp_path / "seg001.mp3"
    seg0.write_bytes(b"")
    seg1.write_bytes(b"")

    dummy = DummyModel()
    full_text, segments = asyncio.run(transcribe_file(
        dummy,
        mp3_full_path=str(seg0),  # not used because bypass_split=True
        work_dir=str(tmp_path),
        seg_seconds=10,
        max_concurrency=2,
        bypass_split=True,
        splitter_fn=lambda *a, **k: None,
        max_segment_retries=0,  # single attempt -> immediate failure placeholder
    ))
    assert len(segments) == 2
    # Expect placeholders with correct timestamps
    lines = [l for l in full_text.split("\n") if l.strip()]
    assert any("[Transcription failed - 00:00:00 - 00:00:10" in l for l in lines)
    assert any("[Transcription failed - 00:00:10 - 00:00:20" in l for l in lines)
    # Ensure reason included
    assert "Reason: boom" in full_text
