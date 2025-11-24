"""Transcriber package root.

Provides modular components for Drive audio transcription pipeline.
"""

import logging

# Package-wide logger. Modules should import `from . import logger` and use it.
logger = logging.getLogger("transcriber")
if not logger.handlers:
    # Default basic configuration; Lambda/host may override
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
