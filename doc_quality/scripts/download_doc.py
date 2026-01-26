# download_doc.py
# /script for downloading documents/
# adriana r.f.
# jan-2026

import argparse
from pathlib import Path
from doc_quality.config.settings import Settings
from doc_quality.pipeline.loader.loader import DocLoader

def main(args, config: Settings):
    print(f"[DOCUMENT QUALITY APP] Downloading documents")
    print(f" > Input file: {args.input}")
    print(f" > Output dir: {args.output}")
    print(f" > Limit (n):  {args.n if args.n > 0 else 'No limit'}")

    loader = DocLoader(config)
    loader.load_batch(
        input_file=str(args.input),
        output_dir=str(args.output),
        n=args.n
    )

if __name__ == "__main__":
    settings = Settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=-1)
    parser.add_argument("--input", type=Path, default=Path(settings.doc_json_path))
    parser.add_argument("--output", type=Path, default=Path(settings.doc_dir))
    args = parser.parse_args()
    main(args, settings)