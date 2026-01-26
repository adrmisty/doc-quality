# topic_modeling.py
# /script for training the topic model/
# adriana r.f.
# jan-2026

import argparse
from pathlib import Path

from doc_quality.config.settings import Settings
from doc_quality.pipeline.topics.trainer import DocTopicTrainer

def main(args, config: Settings):
    print(f"[DOCUMENT QUALITY APP] Topic modeling")
    print(f" > Input meta dir:   {args.input_dir}")
    print(f" > Output model dir: {args.output_dir}")

    trainer = DocTopicTrainer(config)
    trainer.train(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    settings = Settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, default=Path(settings.valid_meta_dir))
    parser.add_argument("--output_dir", type=Path, default=Path(settings.topic_model_dir))
    args = parser.parse_args()
    main(args, settings)