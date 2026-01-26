# extractor.py
# /metadata extraction for downloaded KOs/
# adriana r.f. (arodriguezf@vicomtech.org)
# jan-2026
import json
import os
from pathlib import Path
from tqdm import tqdm
import random
from ...config.settings import Settings
from ..quality.assessment import QualityAssessment
from ..quality.doc_types.doctype import DocType

class DocMetadataExtractor:
    """Process of extraction of metadata from a set of documents."""
    def __init__(self, config: Settings):
        self.config = config
        self.quality_engine = QualityAssessment(config)

    def extract_all(self, input_dir: str, valid_output: str, invalid_output: str, n: int):
        """
        Iterates over a number of n random documents in the input directory, validates their structure, 
        and extracts metadata accordingly.
        Saves results and classifies them into valid/invalid JSON files.
        """
        input_path = Path(input_dir)
        os.makedirs(valid_output, exist_ok=True)
        os.makedirs(invalid_output, exist_ok=True)
        
        # extract from
        files = [f for f in input_path.iterdir() if f.suffix.lower() == '.pdf']
        print(f"[METADATA] Processing {len(files)} files in {input_dir}...")

        if 0 < n < len(files):
            print(f"[METADATA] Randomly selecting {n} files out of {len(files)} available...")
            files = random.sample(files, n)     
        

        for file_path in tqdm(files, unit="file", ncols=80):
            filename = file_path.name
            
            # like with download of docs, pass if already processed
            if self._already_extracted(filename, valid_output, invalid_output):
                continue

            try:
                doc_type = DocType.get_file_type(filename)
            except NotImplementedError:
                self._save(
                    {"filename": filename, "valid_structure": False, "diagnostics": "unsupported extension"}, 
                    invalid_output, filename
                )
                continue

            # validate their structure
            try:
                with open(file_path, "rb") as f:
                    # QualityAssesment.validate calls docpdf.process
                    # which runs your structural score AND calls the metadata client
                    result = self.quality_engine.validate(f, doc_type)
            except Exception as e:
                print(f"(!) Exception extracting meta from {file_path}: {e}")
                continue # next up
            
            # KoQuality --> { "valid": bool, "quality": { "structure": ..., "metadata": ... } }
            record = result.get("quality", {}).get("metadata", {}) or {}
            full_diagnostics = result.get("quality", {}).get("structure", {})
            record["size"] = full_diagnostics.get("stats", {})
            record["valid_structure"] = result["valid"]
            
            # metadata extraction results are either saved into the valid or invalid output directories
            if not result["valid"]:
                record["diagnostics"] = full_diagnostics.get("diagnose", {})
                self._save(record, invalid_output, filename)
            else:
                self._save(record, valid_output, filename)

    def _already_extracted(self, filename: str, valid_dir: str, invalid_dir: str) -> bool:
        json_name = f"{filename}.json"
        return (os.path.exists(os.path.join(valid_dir, json_name)) or 
                os.path.exists(os.path.join(invalid_dir, json_name)))

    def _save(self, data: dict, output_dir: str, filename: str):
        """Saves a single JSON record."""
        out_path = os.path.join(output_dir, f"{filename}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)