# global_state.py
# /holder for global variables for document quality validation, app-wide/
# adriana r.f.
# dec-2025

import logging
from threading import Lock
from typing import Optional

from config.settings import Settings
from pipeline.quality.assessment import QualityAssessment

logger = logging.getLogger(__name__)

_LOCK = Lock()
QUALITY_VALIDATOR: Optional[QualityAssessment] = None


def get_or_init_doc_quality_validator(config: Settings):
    global QUALITY_VALIDATOR
    global _LOCK
    try:
        _LOCK.acquire()
        if QUALITY_VALIDATOR is None:
            logger.info(f'Instantiating document quality validator...')
            QUALITY_VALIDATOR = QualityAssessment(config=config) # just once
    finally:
        _LOCK.release()
    return QUALITY_VALIDATOR