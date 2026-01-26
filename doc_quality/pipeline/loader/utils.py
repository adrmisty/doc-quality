# utils.py
# /utilities for loading documents/
# adriana r.f.
# jan-2026

import json
from typing import Optional, List, Dict, Any

def load_json(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """Loads data structure from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"> Error: Invalid JSON content in file: {file_path}")
                return None
            return data

    except FileNotFoundError:
        print(f"    > Error: JSON file not found: {file_path}")
    except json.JSONDecodeError:
        print(f"    > Error: Invalid JSON format: {file_path}")

    return None