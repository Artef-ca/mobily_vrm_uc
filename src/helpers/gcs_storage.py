from typing import Any
from pathlib import Path
import json
from google.cloud import storage

class GCSStorage:
    def __init__(self, project_id: str, credentials_path: str | None = None):
        if credentials_path:
            self.client = storage.Client.from_service_account_json(credentials_path)
        else:
            self.client = storage.Client(project=project_id)
        self.project_id = project_id

    def read_json(self, bucket_name: str, blob_name: str) -> Any:
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        data = blob.download_as_bytes()
        return json.loads(data.decode("utf-8"))

    def download_to_file(self, bucket_name: str, blob_name: str, dest: str | Path) -> None:
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(dest))
