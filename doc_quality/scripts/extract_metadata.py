# extract_metadata.py
# /script for extracting metadata/
# adriana r.f.
# jan-2026

import argparse
from pathlib import Path
from doc_quality.config.settings import Settings
from doc_quality.pipeline.metadata.extractor import DocMetadataExtractor

def main(args, config: Settings):
    print(f"[DOCUMENT QUALITY APP] Metadata extraction")
    print(f" > Input dir:     {args.input_dir}")
    print(f" > Valid meta dir:     {args.output_valid}")
    print(f" > Invalid meta dir:   {args.output_invalid}")
    print(f" > Max docs meta to extract:   {args.n_meta}")

    extractor = DocMetadataExtractor(config)
    extractor.extract_all(
        input_dir=str(args.input_dir),
        valid_output=str(args.output_valid),
        invalid_output=str(args.output_invalid),
        n=int(args.n_meta)
    )

if __name__ == "__main__":
    settings = Settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, default=Path(settings.doc_dir))
    parser.add_argument("--output_valid", type=Path, default=Path(settings.valid_meta_dir))
    parser.add_argument("--output_invalid", type=Path, default=Path(settings.invalid_meta_dir))
    parser.add_argument("--n_meta", type=int, default=-1, help="Max n documents to extract metadata from")
    args = parser.parse_args()
    main(args, settings)