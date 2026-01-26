# docpdf.py
# /[strategy] processing of PDF documents/
# adriana r.f.
# jan-2026
import re
from typing import IO
from pypdf import PdfReader
from ....config.settings import Settings
from ...metadata.client import DocMetadataClient
from .doc import Document, DocQuality

class DocPdf(Document):
    """Processing of a document of type PDF."""
    MIN_PAGES = 2
    MIN_BYTES = 50_000
    MIN_TEXT_LEN = 500
    MIN_AVG_CHARS = 20
    MIN_LINE_LEN = 15
    MIN_TITLE_LEN = 5
    MAX_TITLE_LEN = 500
    MAX_SUBTITLE_LEN = 300
    
    def __init__(self, config: Settings):
        self.config = config

    def process(self, file: IO) -> DocQuality:
        """Determines structural quality results for a given document of PDF type."""
        text, initial_stats = self._read(file)
        
        score, diagnostics, full_stats = self._diagnose(text, initial_stats)
        
        is_valid = (score >= 6)
        metadata = {}

        # metadata is only extracted if document structurally valid
        if is_valid:
            metadata = DocMetadataClient.extract(file=file, config=self.config)       

            if not metadata.get("title") and not metadata.get("topic"):
                is_valid = False
                diagnostics["metadata"] = "structurally invalid or unrelated"
        
        return DocQuality(
            is_struct_valid=is_valid,
            text=text,
            metadata=metadata,
            diagnostics={"diagnose": diagnostics, "stats": full_stats}
        )

    # -------------------------------------------------------------------------

    def _read(self, file: IO) -> tuple[str, dict]:
        """Reads a PDF and extracts its textual content, and size information."""
        try:
            file.seek(0)
            header = file.read(5)
            file.seek(0)
            
            if b"%PDF-" not in header: # must be a PDF!!!!
                print(f"    > Warning: Invalid PDF signature [{header}]\n")
                return "", {"num_pages": 0, "bytes": 0}

            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            reader = PdfReader(file)
            
            if reader.is_encrypted:
                print(f"    > Warning: PDF is encrypted and cannot be read\n")
                return "", {"num_pages": 0, "bytes": size}

            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            return text, {"num_pages": len(reader.pages), "bytes": size}

        except Exception as e:
            print(f"    > Warning: error while reading PDF: {e}\n")
            return "", {"num_pages": 0, "bytes": 0}
        
    # -------------------------------------------------------------------------

    def _diagnose(self, text: str, stats: dict) -> tuple[int, dict, dict]:
        """Analyzes structural quality and returns score, diagnostics, and detailed stats."""
        score = 0
        diagnose = {}
        clean_text = text.strip()
        lines = clean_text.splitlines()

        # include structural stats into both valid and invalid outputs
        text_len = len(clean_text)
        avg_line_len = (sum(len(l) for l in lines) / len(lines)) if lines else 0
        stats.update({
            "text_len": text_len,
            "avg_line_len": round(avg_line_len, 2),
            "num_lines": len(lines)
        })

        # ** SCORING LOGIC **
        #TODO: discuss structural quality threshold values

        # 1. page count (x2 points)
        if stats["num_pages"] >= self.MIN_PAGES:
            score += 2
        else:
            diagnose["num_pages"] = f"too few (<{self.MIN_PAGES})"
        
        # 2. file size (x1 point)
        if stats["bytes"] > self.MIN_BYTES:
            score += 1
        else:
            diagnose["file_size"] = "too small"

        # 3. length of whole text (x2 points)
        if text_len > self.MIN_TEXT_LEN:
            score += 2
            # bonus for dense single pages
            if stats["num_pages"] < self.MIN_PAGES:
                score += 0.5
                diagnose["text_density"] = "single page, but dense"
        else:
            diagnose["text_length"] = "too short"

        # 4. average line length (x1 point)
        if avg_line_len > self.MIN_LINE_LEN:
            score += 1
        else:
            diagnose["avg_line_length"] = "short lines; likely artifacts"

        # 5. title heuristic (first line) (x1 point)
        # TODO: fix recognition of title/subtitle
        if lines:
            first_line = lines[0].strip()
            if self.MIN_TITLE_LEN < len(first_line) < self.MAX_TITLE_LEN and not re.match(r"^https?://", first_line):
                score += 1
            else:
                diagnose["title_check"] = "missing or unusual"
        else:
            diagnose["title_check"] = "no text lines"

        # 6. subtitle heuristic (second line) (x1 point)
        if len(lines) > 1:
            second_line = lines[1].strip()
            if len(second_line) < self.MAX_SUBTITLE_LEN:
                score += 1
            else:
                diagnose["subtitle_check"] = "too long"
        elif len(lines) == 1:
            score = -1
            pass 

        return score, diagnose, stats