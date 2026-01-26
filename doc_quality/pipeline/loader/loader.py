# loader.py
# /batch-loads documents from an external source/
# adriana r.f.
# jan-2026

import os
from tqdm import tqdm
from ...config.settings import Settings
from .downloader import DocDownloader
from .utils import load_json

class DocLoader:
    """Batch loader of documents from a file with the URLs of these files."""

    def __init__(self, config: Settings):
        self.config = config
        self.downloader = DocDownloader(config)

    def load_batch(self, input_file: str, output_dir: str, n: int = None, load_type: str = "application/pdf") -> None:
        """Loads {n} documents from the URLs on a JSON file into the output directory."""
        os.makedirs(output_dir, exist_ok=True)

        ko_data = load_json(input_file)
        if not ko_data:
            print("    > Warning: No KO data found.")
            return

        max_load = n if (isinstance(n, int) and n > 0) else None
        loaded_count = 0
        
        total = max_load if max_load else len(ko_data)
        pbar = tqdm(total=total, unit="file", ncols=80, disable=False) # progress bar!

        for record in ko_data:
            if max_load is not None and loaded_count >= max_load:
                break

            processed_urls = set()

            # main @id
            # "@id": "URL"
            main_url = record.get("@id")
            if self._process_url(main_url, processed_urls, output_dir, load_type):
                loaded_count += 1
                pbar.update(1)

            # keep it under the maximum
            if max_load is not None and loaded_count >= max_load:
                break

            # "doc_resources": [{
            # "@id": "URL",
            for res in record.get("doc_resources", []):
                if max_load is not None and loaded_count >= max_load:
                    break

                res_url = res.get("@id")
                mime_type = res.get("display_metadata", {}).get("hosted_mime_type")
                if (not mime_type or mime_type == load_type):
                    if self._process_url(res_url, processed_urls, output_dir, load_type):
                        loaded_count += 1
                        pbar.update(1)

        pbar.close()

    def _process_url(self, url: str, history: set, dest: str, type_filter: str) -> bool:
        """Downloads document off an URL based on supported file type and whether already downloaded."""
        if url and url not in history:
            if self.downloader.fetch(url, dest, type_filter):
                history.add(url)
                return True
        return False