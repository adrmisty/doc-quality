# downloader.py
# /downloads document with http into file system/
# adriana r.f.
# jan-2026

import os
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from ...config.settings import Settings

class DocDownloader:
    """Downloading of documents in a HTTP session."""

    def __init__(self, config: Settings):
        self.config = config
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        """Configures a requests session with retry logic."""
        retry_cfg = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_cfg)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch(self, url: str, output_dir: str, expected_type: str) -> Optional[str]:
        """
        Downloads a file from a URL to the output directory.
        (Like with metadata extraction) Skips download if file already exists.
        """
        if not url:
            return None

        try:
            filename = self._get_filename(url, expected_type)
            save_path = os.path.join(output_dir, filename)

            # if already downloaded, pass
            if os.path.exists(save_path):
                print(f"    > Already downloaded: {filename}")
                return save_path

            # otherwise, download it off the internet
            with self.session.get(url, stream=True, timeout=20) as response:
                response.raise_for_status()
                
                print(f"____> Downloading: {filename}")
                with open(save_path, 'wb') as fh:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            fh.write(chunk)
            
            return save_path

        except requests.exceptions.RequestException as e:
            print(f"    > Error: downloading '{url}': {e}")
        except Exception as e:
            print(f"    > Error: unexpected downloading '{url}': {e}")
        
        return None

    def _get_filename(self, url: str, load_type: str) -> str:
        """Gets a valid filename for a given document's URL."""
        parsed = urlparse(url)
        raw_name = os.path.basename(parsed.path)
        
        # default extension, none (but we expect PDF for now?)
        ext = load_type.split("/")[-1] if "/" in load_type else "bin"

        if not raw_name:
            safe_url = url.replace("https://", "").replace("http://", "").replace("/", "_")
            filename = f"{safe_url[:50]}.{ext}"
        else:
            filename = raw_name
            if "." not in filename:
                filename = f"{filename}.{ext}"

        # use a hash for the name just in case
        if not filename:
            filename = f"file_{hash(url) & 0xfffffff}.{ext}"
            
        return filename