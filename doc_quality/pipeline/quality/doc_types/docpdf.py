# docpdf.py
# /[strategy] processing of PDF documents (typology-dependent)/
# adriana r.f.
# feb-2026
import re
from typing import IO
from pypdf import PdfReader
from ....config.settings import Settings
from ...metadata.client import DocMetadataClient
from .doc import Document, DocQuality

# --- CONSTANTS & HEURISTIC THRESHOLDS ---
# TODO: to-be-defined by WP4
MIN_SCORE = 6 # 5 criteria so far, each one valid accordingly

MIN_BYTES = 20_000  # 20KB
MIN_TEXT_LEN = 300  # total minimum text
MAX_TEXT_LEN = 10_000

TITLE_MIN_LEN = 5
TITLE_MAX_LEN = 300
SUBTITLE_MAX_LEN = 400
AVG_CHARS = 200

LINE_LEN = 20

MAX_BRIEF_PAGES = 5

MAX_SCIENTIFIC_PAGES = 15
MIN_SCIENTIFIC_PAGES = 3

MIN_DELIVERABLE_PAGES = 6
MIN_REPORT_PAGES = 50

MAX_PROMO_PAGES = 4

NOISE_RE = [
    r"^page\s+\d+$",            # page no.
    r"^\d+\s*$",                # no.
    r"^https?://",              # URLs
    r"^www\.",                  # domains
    r"^issn\s+[\d\-x]+",        # ISSN codes
    r"^draft$",                 # watermaks
    r"^©",                      # copyright
    r"^\d{1,2}/\d{1,2}/\d{2,4}" # dates
]

HEADER_SKIP_RE = [
    r"received funding from",
    r"grant agreement",
    r"horizon 2020",
    r"project acronym",
    r"project no",
    r"dissemination level",
    r"call identifier"
]

KEYWORDS = {
        "BRIEF": [
            "practice abstract", "policy brief", "factsheet", "executive summary", 
            "practical", "solution", "outcome", "roadmap", "recommendations",
            "about this abstract", "about the project", "further information", "more info"
        ],
        "PROMO": [
            "newsletter", "news", "boletín", "kick-off", "meeting", "seminar", 
            "highlights", "agenda", "save the date"
        ],
        "PROJECT": [
            "deliverable", "grant agreement", "work package", "due date", 
            "submission date", "conceptual framework", "guidelines", "best practice",
            "training module", "tutorial", "instructions", "handbook", "manual", "guide",
            "educational material", "lesson plan", "curriculum", "syllabus", "training kit"
        ],
        "SCIENTIFIC": [
            "thesis", "dissertation", "journal", "proceedings", "conference"
        ],
        "FUNDING": [
            "funded", "funds", "received funding from", "horizon 2020", "horizon europe", "grant agreement"
        ]
    }

class DocPdf(Document):
    """Processing of a Knowledge Object of type PDF."""
    
    def __init__(self, config: Settings):
        self.config = config
        self.noise_patterns = [re.compile(p, re.IGNORECASE) for p in NOISE_RE]
        self.skip_patterns = [re.compile(p, re.IGNORECASE) for p in HEADER_SKIP_RE]

    def process(self, file: IO) -> DocQuality:
        """Determines structural quality results for a given document of PDF type."""
        
        # read the PDF + gather size/text statistics
        # then, classify the document according to its typology
        text, stats = self._read(file)
        assigned_type = self._classify_typology(text, stats)
        stats["type"] = assigned_type
        
        # once stats+text are processed and typology assigned
        score, diagnostics, full_stats = self._diagnose(text, stats, assigned_type)
        
        is_valid = (score >= MIN_SCORE)
        
        # critical fails:
        # unassigned type + extremely sparse document
        if assigned_type == "UNKNOWN":
            is_valid = False
            diagnostics["typology_check"] = "could not match EUFB typology"
            score = 0 
        
        avg_chars_per_page = stats["text_len"] / max(1, stats["num_pages"])
        if stats["num_pages"] > 2 and avg_chars_per_page < AVG_CHARS:
            is_valid = False
            diagnostics["content_check"] = "document appears to be empty tables or sparse text"
            score = 0
        
        # only extract metadata if preliminary valid structure
        metadata = {}
        if is_valid:
            metadata = KoMetadataClient.extract(
                file=file, 
                config=self.config
            )       

            # TODO: check which else to include in this check
            if not metadata.get("title") and not metadata.get("topic"):
                is_valid = False
                diagnostics["metadata"] = "structurally valid but [wrt. extracted metadata] semantically invalid"
        
        return KoQuality(
            is_struct_valid=is_valid,
            text=text,
            metadata=metadata,
            diagnostics={"diagnose": diagnostics, "stats": full_stats, "score": score}
        )
        
    # ---------------------------------------------------------------------------------------        

    def _classify_typology(self, text: str, stats: dict) -> str:
        """Preliminarily determines document category based on structural hints and patterns."""
        num_pages = stats.get("num_pages", 0)
        
        # 1. Prepare segments (Focus on relevant areas to reduce noise)
        # start: titles, abstracts, document codes                       
        text_start = text[:5000].lower() 
        # end: references, appendices, contact info
        text_end = text[-5000:].lower()
        full_sample = " ".join((text_start + " " + text_end).split())
        
        # --- DEFINING FEATURE DETECTORS start ---

        def _has_any(keywords):
            return any(k in full_sample for k in keywords)

        # ** SCIENTIFIC **
        # headers for main scientific sections
        has_ref = bool(re.search(r"(?m)^\s*(references|bibliography)\s*$", text_end))
        has_sci_sections = bool(re.search(r"(?m)^\s*(abstract|introduction|methodology)\s*$", text_start))        
        if has_ref and has_sci_sections:
            return "SCIENTIFIC / TECHNICAL PAPER"

        # ** BRIEFS AND ABSTRACTS**
        # self-identified
        # shorter
        # grant agreement info
        # template-based
        # they usually have policy brief/recommendations/so on in their title
        is_brief = _has_any(KEYWORDS["BRIEF"])
        if num_pages <= MAX_BRIEF_PAGES and is_brief:
            return "POLICY BRIEF / PRACTICE ABSTRACT"

        # ** PROMOS ** very short docs
        is_promo = _has_any(KEYWORDS["PROMO"])
        if num_pages <= MAX_PROMO_PAGES and is_promo:
            return "PROMOTIONAL / NEWSLETTER"

        # ** REPORTS & BOOKS ** also guides and deliverables as a whole
        has_toc = bool(re.search(r"(?m)^\s*(table of contents|contents|index)\s*$", text_start))
        is_project = _has_any(KEYWORDS["PROJECT"]) or has_toc
        if is_project or (num_pages >= MIN_DELIVERABLE_PAGES and (has_toc or "version" in text_start)):
            return "PROJECT DELIVERABLE" 


        # length-based defaults
        if num_pages > MIN_REPORT_PAGES: return "PROJECT REPORT" # long documents probaly reports
        if num_pages <= MAX_PROMO_PAGES: return "PROMOTIONAL / FLYER" # flyer with no keywords detected
        
        # final fail
        return "UNKNOWN"
        
    # ---------------------------------------------------------------------------------------
    # structural validity diagnosis
    
    def _diagnose(self, text: str, stats: dict, typology: str) -> tuple[int, dict, dict]:
        """Typology-based analysis ensuring consistency with process() and constants."""
        score = 0
        diagnose = {}
        
        headers = self._extract_titles(text)
        stats["headers"] = headers 
        
        clean_text = headers["clean_text"]
        text_len = len(clean_text)
        lines = clean_text.splitlines()
        
        avg_line_len = (sum(len(l) for l in lines) / len(lines)) if lines else 0
        
        if "clean_text" in headers:
            del headers["clean_text"] # so as not to appear in output

        stats["headers"] = headers 
        stats.update({
            "text_len": text_len,
            "avg_line_len": round(avg_line_len, 2),
            "num_lines": len(lines)
        })
        
        # --- TYPOLOGY-BASED SCORING ---
        
        # ** PAGE COUNT **
        pg_count = stats["num_pages"]
        
        if "PROMOTIONAL" in typology:
            if pg_count <= MAX_PROMO_PAGES: score += 2 
            else: diagnose["typology_mismatch"] = f"promotional material too long (>{MAX_PROMO_PAGES} pages)"
            
        elif typology == "SCIENTIFIC / TECHNICAL PAPER":
            if pg_count >= MIN_SCIENTIFIC_PAGES: score += 2
            else: diagnose["typology_mismatch"] = f"scientific paper too short (<{MIN_SCIENTIFIC_PAGES} pages)"
            
            if pg_count > MAX_SCIENTIFIC_PAGES:
                # warning only (score penalty), not invalidation
                score -= 1
                diagnose["typology_warning"] = f"scientific paper unusually long (>{MAX_SCIENTIFIC_PAGES} pages)"
                
        elif typology == "POLICY BRIEF / PRACTICE ABSTRACT":
            if pg_count <= MAX_BRIEF_PAGES: score += 2
            else: diagnose["typology_mismatch"] = f"brief/abstract too long (>{MAX_BRIEF_PAGES} pages)"
            
        elif typology == "PROJECT DELIVERABLE":
            if pg_count >= MIN_DELIVERABLE_PAGES: score += 2
            else: diagnose["typology_mismatch"] = f"deliverable too short (<{MIN_DELIVERABLE_PAGES} pages)"
            
        elif typology == "PROJECT REPORT":
            if pg_count >= MIN_REPORT_PAGES: score += 2
            else: diagnose["typology_mismatch"] = f"volume/report too small (<{MIN_REPORT_PAGES} pages)"
            
        elif typology == "UNKNOWN":
            diagnose["typology"] = "unknown document structure"
            return 0, diagnose, stats

        # ** FUNDING STATEMENT **
        text_lower = text.lower()
        if any(k in text_lower for k in KEYWORDS["FUNDING"]):
            score += 1
            diagnose["funding_check"] = "valid EU Funding statement found"

        # ** FILE SIZE **
        if stats["bytes"] > MIN_BYTES:
            score += 1
        else:
            diagnose["file_size"] = "file too small or empty"

        # ** TEXT DENSITY **
        if text_len > MIN_TEXT_LEN:
            score += 2
            # bonus for big documents with a lot of text
            if typology in ["SCIENTIFIC / TECHNICAL PAPER", "PROJECT REPORT", "PROJECT DELIVERABLE"] and text_len > MAX_TEXT_LEN:
                score += 1
        else:
            diagnose["text_density"] = "not enough text content"

        # ** LINE LENGTH **
        if avg_line_len > LINE_LEN: 
            score += 1
        else:
            diagnose["text_quality"] = "broken text or bad OCR (short lines)"

        # ** TITLE **
        if headers["title"]:
            score += 1
            if headers["subtitle"]: score += 0.5
        else:
            diagnose["title"] = "title not identifiable"

        return score, diagnose, stats

    # ---------------------------------------------------------------------------------------
    # working on actual physical properties of the document

    def _read(self, file: IO) -> tuple[str, dict]:
        """Reads PDF safely."""
        try:
            file.seek(0)
            header = file.read(5)
            file.seek(0)
            
            if b"%PDF-" not in header:
                return "", {"num_pages": 0, "bytes": 0}

            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            reader = PdfReader(file)
            if reader.is_encrypted:
                return "", {"num_pages": 0, "bytes": size}

            text_parts = []
            has_images = False # TODO: check image extraction
            
            for p in reader.pages:
                extracted = p.extract_text()
                if extracted:
                    text_parts.append(extracted)
                if '/XObject' in p.get('/Resources', {}):
                    has_images = True
            
            text = "\n".join(text_parts)
            return text, {"num_pages": len(reader.pages), "bytes": size, "has_images": has_images}

        except Exception:
            return "", {"num_pages": 0, "bytes": 0}


    def _extract_titles(self, text: str) -> Dict[str, str]:
        """More robust extraction of title/subtitle ignoring noise
        (rather than text[0]....... very lazy).
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        title = None
        subtitle = None
        
        scan_limit = min(len(lines), 20) 
        title_i = -1
        
        for i in range(scan_limit):
            line = lines[i]
            
            # noise: (page numbers, URLs)
            if any(p.search(line) for p in self.noise_patterns): continue
            
            # artifacts: (tiny lines)
            if len(line) < 3: continue

            # EU funding
            if any(p.search(line) for p in self.skip_patterns): continue
            
            # title
            if not title:
                if TITLE_MIN_LEN <= len(line) <= TITLE_MAX_LEN:
                    title = line
                    title_i = i
                continue
                
            # adjacent subtitle
            if title and not subtitle:
                if i == title_i + 1:
                    if len(line) <= SUBTITLE_MAX_LEN:
                        subtitle = line
                        break

        return {"clean_text": text.strip(), "title": title, "subtitle": subtitle}
