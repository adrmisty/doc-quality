# doc.py
# /(decoupled) processing of knowledge objects/
# adriana r.f.
# jan-2026
from abc import ABC, abstractmethod
from typing import IO, Dict, Any
from dataclasses import dataclass

@dataclass
class DocQuality:
    is_struct_valid: bool
    text: str
    metadata: Dict[str, Any]
    diagnostics: Dict[str, Any]

class Document(ABC):
    """Processing of different, supported Knowledge Object file types."""
    
    @abstractmethod
    def process(self, file: IO) -> DocQuality:
        """Extracts text, metadata and validates structural integrity, in order to retrieve doc Quality results for a given document."""
        pass # respective impl. in each doc{mimetype}.py class, e.g. [docpdf.py]