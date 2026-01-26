# pipeline.py
# /full pipeline execution/
# adriana r.f.
# jan-2026

from argparse import Namespace

from doc_quality.config.settings import Settings

from doc_quality.scripts.download_doc import main as run_download
from doc_quality.scripts.extract_metadata import main as run_metadata
from doc_quality.scripts.topic_modeling import main as run_topics

def main(args, config: Settings):
    print("=========================================")
    print("             DOC QUALITY PIPELINE        ")
    print("=========================================")

    # first up, download all files
    dl_args = Namespace(
        input=args.json_source,
        output=args.pdf_dir,
        n=args.n
    )
    run_download(dl_args, config)
    print("\n-----------------------------------------\n")

    # then, extract their metadata
    meta_args = Namespace(
        input_dir=args.pdf_dir,
        output_valid=args.valid_dir,
        output_invalid=args.invalid_dir
    )
    run_metadata(meta_args, config)
    print("\n-----------------------------------------\n")

    # based on this metadata, run topic modeling
    topic_args = Namespace(
        input_dir=args.valid_dir,
        output_dir=args.topic_dir
    )
    run_topics(topic_args, config)
    
    print("\n=========================================")
    print("        PIPELINE COMPLETED               ")
    print("=========================================")
    