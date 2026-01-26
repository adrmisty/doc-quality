# client.py
# /client for external metadata extraction service/
# adriana r.f.
# jan-2026

import os
import json
import requests
from typing import IO
from pathlib import Path
from ...config.settings import Settings

class DocMetadataClient:
    """Metadata extraction for a (structurally-valid) document."""
    
    @classmethod
    def extract(cls, file: IO, config: Settings, filename: str = None) -> dict:
        """Streams a file to the external metadata extraction endpoint."""
        file.seek(0)
        
        response_base = {}

        try:
            dummy = "polloconpatatas.pdf"
            files = {"file": (dummy, file, "application/pdf")}

            if os.path.exists(config.prompt_path):
                prompt = Path(config.prompt_path).read_text(encoding="utf-8")
            else:
                prompt = "" 

            data = {"prompt": prompt}
            
            headers = {}
            if hasattr(config, "api_key") and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
                        
            api_resp = requests.post(
                config.extraction_endpoint,
                headers=headers,
                files=files, 
                data=data, 
                timeout=60
            )
            api_resp.raise_for_status()
            
            result = api_resp.json()
            
            return {**response_base, **result}

        except requests.exceptions.RequestException as e:
            print(f"    (!) > Error extracting metadata: {e}")
            return {**response_base, "diagnostics": {"error": "endpoint connection failed"}}
            
        except json.JSONDecodeError:
            print(f"    (!) > Error decoding metadata JSON response")
            return {**response_base, "diagnostics": {"error": "invalid json response"}}
            
        except Exception as e:
            print(f"    (!) > Unexpected error: {e}")
            return {**response_base, "diagnostics": {"error": f"unknown metadata extraction error ({e})"}}