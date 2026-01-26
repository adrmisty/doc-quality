# settings.py
# /settings and constants for the QA app/
# adriana r.f.
# jan-2026

from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    ############## APP
    app_fqn: str = 'app.fastapi_app:app'
    api_title: str = 'Document quality validation'
    api_description: str = 'Service to extract metadata information from documents and align them in a topic model space'
    api_root_path: str = '/project'
    api_prefix: str = '/v1/doc-quality'
    ############## PORT
    api_port: int = 30600
    api_log_level: str = 'debug'
    ############## METADATA
    prompt_path : Path = ROOT_DIR / "config" / "prompt.txt"
    extraction_endpoint : str = "metadata_extraction_endpoint_url}"
    ############## BERTOPIC
    topic_model: Path = ROOT_DIR / "data" / "topic"
    embedding_model : str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2" # same as the one used in topic model training
    llm_model : str = "Qwen/Qwen2.5-7B-Instruct"
    min_topic_prob: float = 0.5
    topic_targets: list = ["topic1", "topic2", "..."] 
    ############## PROJECT
    project_name: str = 'Doc Quality Assessment'
    ############## DIRECTORIES
    ko_dir : Path = ROOT_DIR / "data" / "pdf/"
    ko_json_path : Path = ROOT_DIR / "data" / "{FILE WITH DOC URLS}.json"
    valid_meta_dir : Path = ROOT_DIR / "data" / "metadata" / "valid_meta/"
    invalid_meta_dir : Path = ROOT_DIR / "data" / "metadata" / "invalid_meta/"
    topic_model_dir : Path = ROOT_DIR / "data" / "models" / "bertopic/"
    
@lru_cache()
def get_settings():
    return Settings()
