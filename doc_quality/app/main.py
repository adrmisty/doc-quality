# main.py
# /CLI for document quality assessment logic scripts & entire app/
# adriana r.f.
# jan-2026

import argparse
import uvicorn
from pathlib import Path

from doc_quality.config.settings import Settings
from doc_quality.scripts.download_doc import main as download
from doc_quality.scripts.extract_metadata import main as metadata
from doc_quality.scripts.topic_modeling import main as topics
from doc_quality.scripts.full_pipeline import main as full_pipeline

settings = Settings()

parser = argparse.ArgumentParser(description="Quality Assessment logic & app")
sub = parser.add_subparsers(dest="command", required=True, help="Available commands")

# --- DOWNLOAD ---
p_dl = sub.add_parser("download", help="Download document PDFs")
p_dl.add_argument("--n", type=int, default=-1, help="Max PDFs to download")
p_dl.add_argument("--input", type=Path, default=Path(settings.ko_json_path), help="Input JSON file with URLs")
p_dl.add_argument("--output", type=Path, default=Path(settings.ko_dir), help="PDF Output directory")

# --- METADATA ---
p_meta = sub.add_parser("metadata", help="Extract metadata from PDFs")
p_meta.add_argument("--input_dir", type=Path, default=Path(settings.ko_dir), help="PDF Input directory")
p_meta.add_argument("--output_valid", type=Path, default=Path(settings.valid_meta_dir), help="Valid JSON output")
p_meta.add_argument("--output_invalid", type=Path, default=Path(settings.invalid_meta_dir), help="Invalid JSON output")
p_meta.add_argument("--n_meta", type=int, default=-1, help="Max KOs to extract metadata from")

# --- TOPICS ---
p_top = sub.add_parser("topics", help="Run topic modeling on valid metadata")
p_top.add_argument("--input_dir", type=Path, default=Path(settings.valid_meta_dir), help="Input directory of valid metadata JSONs")
p_top.add_argument("--output_dir", type=Path, default=Path(settings.topic_model_dir), help="Output directory for topic model")

# --- FULL PIPELINE (ALL) ---
p_all = sub.add_parser("all", help="Run full pipeline: download -> metadata -> topics")
p_all.add_argument("--n", type=int, default=-1)
p_all.add_argument("--json_source", type=Path, default=Path(settings.ko_json_path))
p_all.add_argument("--pdf_dir", type=Path, default=Path(settings.ko_dir))
p_all.add_argument("--valid_dir", type=Path, default=Path(settings.valid_meta_dir))
p_all.add_argument("--invalid_dir", type=Path, default=Path(settings.invalid_meta_dir))
p_all.add_argument("--topic_dir", type=Path, default=Path(settings.topic_model_dir))

# --- SERVE (APP) ---
p_srv = sub.add_parser("serve", help="Run the FastAPI backend server")
p_srv.add_argument("--host", type=str, default="0.0.0.0")
p_srv.add_argument("--port", type=int, default=settings.api_port)
p_srv.add_argument("--reload", action="store_true", help="Enable auto-reload")

# from CLI root:
# (CUDA_VISIBLE_DEVICES=x) python3 -m doc_quality.app.main [whatever command with whatever params]

# with Docker: 
# docker compose build
# docker-compose run --rm doc_quality python3 -m doc_quality.app.main download

def main():
    args = parser.parse_args()
    
    config = settings 

    if args.command == "download":
        download(args, config)
        
    elif args.command == "metadata":
        metadata(args, config)
        
    elif args.command == "topics":
        topics(args, config)
        
    elif args.command == "all":
        full_pipeline(args, config)
        
    elif args.command == "serve":
        print(f"[DOC QUALITY APP] Starting {config.app_fqn} on {args.host}:{args.port}...")
        uvicorn.run(
            settings.app_fqn, 
            host=args.host, 
            port=args.port, 
            log_level=settings.api_log_level.lower(), 
            proxy_headers=True, 
            workers=1,
            reload=args.reload
        )
if __name__ == "__main__":
    main()