# utils.py
# /preprocessing/IO utils for topic modeling/
# adriana r.f.
# jan-2026

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
from bertopic import BERTopic

def load_docs(input_dir: Path, metadata_fields: List[str], min_text_len: int = 10) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Loads extracted metadata text for specific fields."""
    docs = []
    doc_ids = []
    meta = []

    # only valid metadata in JSON format
    files = list(input_dir.glob("*.json"))
    print(f"    > [Topic modeling] Loading metadata texts from {len(files)} files...")

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            
            # this is what will be passed for the model
            text_parts = []
            record = {}
            for field in metadata_fields:
                val = data.get(field, "")
                record[field] = val
                if isinstance(val, list):
                    val = ", ".join(map(str, val))
                if isinstance(val, str) and val.strip():
                    text_parts.append(val)

            text = ". ".join(text_parts).strip()

            if len(text) > min_text_len:
                docs.append(text)
                doc_ids.append(f.name)
                meta.append(record)

        except:
            continue

    return docs, doc_ids, meta

def save_model(topic_model: BERTopic, output_dir: Path, docs: List[str], filenames: List[str]):
    """Saves trained BERTopic model and metadata CSVs."""
    
    print(f"    > [Topic modeling] Saving model to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # make sure the custom name mappings are saved
    topic_info = topic_model.get_topic_info()
    if "CustomName" in topic_info.columns:
        topic_info["Name"] = topic_info["CustomName"]
    topic_info.to_csv(output_dir / "topic_info.csv", index=False)

    doc_info = topic_model.get_document_info(docs)
    doc_info["filename"] = filenames 
    doc_info.to_csv(output_dir / "document_mapping.csv", index=False)

    # safetensors works best for app
    model_path = output_dir / "model"
    topic_model.save(
        str(model_path), 
        serialization="safetensors", 
        save_embedding_model=True,
        save_ctfidf=True
    )