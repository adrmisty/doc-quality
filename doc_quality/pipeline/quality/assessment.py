# assessment.py
# /document assessment: structural and semantic quality of documents/
# adriana r.f.
# jan-2026

from typing import IO
from ...config.settings import Settings
from .doc_types.doctype import DocType
from .doc_types.docpdf import DocPdf
from .topics import DocTopic

class QualityAssessment:
    """Automatically assesses quality of a document, regarding structure and semantics."""
    def __init__(self, config: Settings):
        self.config = config
        
        try:
            self.topics = DocTopic(config=config)
        except Exception as e:
            print(f"    > Error loading model from from {self.config.topic_model}, must be trained first: {e}")

        # KO type processing // strategy+factory
        self.ko_file_types = {
            DocType.PDF: DocPdf(config),
            #TODO: KoType.PPT: KoPpt(config)
        }

    def validate(self, file: IO, file_type: DocType) -> dict:
        """Assesses the quality of a document regarding its structure and text stats, and its semantic relevance within the topic model space."""
        ko = self.ko_file_types.get(file_type)
        if not ko:
            return {"valid": False, "diagnose": f"unsupported file type: {file_type.value}"}

        # ** STRUCTURAL VALIDATION **
        # if structurally valid, respective metadata is extracted
        result = ko.process(file)
        full_diagnostics = {
            "structure": result.diagnostics, 
            "metadata": result.metadata
        }
        
        # ** SEMANTIC VALIDATION **
        # once metadata is extracted, 
        is_sem_valid = False
        if result.is_struct_valid:
            is_sem_valid, sem_diag = self.topics.get_topic(result.metadata)
            full_diagnostics["topic"] = sem_diag

        return {
            "valid": result.is_struct_valid and is_sem_valid,
            "quality": full_diagnostics,
        }