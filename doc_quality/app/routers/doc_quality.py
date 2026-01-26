# ko_quality.py
# /router and endpoint for document Quality validation/
# adriana r.f.
# jan-2026

import logging

from fastapi import APIRouter, UploadFile

from config.settings import Settings
from app.global_state import get_or_init_doc_quality_validator
from doc_quality.pipeline.quality.doc_types.doctype import DocType

router = APIRouter()

logger = logging.getLogger(__file__)
    
@router.post("/quality", summary="Quality assessment (structure + topic relevance) of a document")
async def validate_quality(file: UploadFile):
    """Validates a document in terms of its structure and the alignment of its semantics and content within a topic model space."""
    ko_quality_validator = get_or_init_doc_quality_validator(config=Settings())
    return ko_quality_validator.validate(file=file.file, 
                                        file_type=DocType.get_file_type(file_name=file.filename))
