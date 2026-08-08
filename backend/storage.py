"""
Storage adapter with local and Google Cloud Storage backends.

Design rationale:
- The system uses a storage abstraction layer so the backend can switch between
  local file storage (for development/demo) and Google Cloud Storage (for production)
  without changing application logic.
- This demonstrates the cloud-native architecture described in the project proposal:
  documents are stored in cloud storage with region-aware placement.

Cloud Justification:
- Google Cloud Storage (GCS) provides durable, scalable object storage with
  multi-region and regional bucket options. This aligns with our cost-aware and
  carbon-aware region selection feature.
- Local mode is used for development and demonstration without incurring cloud costs.
"""

import os
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Storage configuration from environment variables
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")  # "local" or "gcs"
LOCAL_STORAGE_PATH = os.environ.get("LOCAL_STORAGE_PATH", os.path.join(os.path.dirname(__file__), "uploads"))
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "")
GCS_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")


class StorageAdapter:
    """Abstract storage interface for document storage operations."""

    def upload(self, file_data: bytes, file_name: str, region: str) -> dict:
        raise NotImplementedError

    def download(self, file_path: str) -> bytes:
        raise NotImplementedError

    def delete(self, file_path: str) -> bool:
        raise NotImplementedError


class LocalStorage(StorageAdapter):
    """
    Local filesystem storage backend.
    Used for development and demo purposes.
    Simulates region-based storage by creating subdirectories per region.
    """

    def __init__(self):
        os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
        logger.info(f"LocalStorage initialized at {LOCAL_STORAGE_PATH}")

    def upload(self, file_data: bytes, file_name: str, region: str) -> dict:
        """
        Store file in a region-specific local directory.
        This simulates storing documents in different cloud regions.

        The 'region' parameter comes from the cost-aware or carbon-aware
        selection in regions.py. For example:
        - Cost-aware mode routes to 'europe-west1' (cheapest)
        - Carbon-aware mode routes to 'europe-north1' (greenest)

        Each region gets its own subdirectory, simulating separate
        cloud data centre locations.
        """
        region_path = os.path.join(LOCAL_STORAGE_PATH, region)
        os.makedirs(region_path, exist_ok=True)

        file_path = os.path.join(region_path, file_name)
        with open(file_path, "wb") as f:
            f.write(file_data)

        logger.info(f"File '{file_name}' stored in local region: {region}")
        return {
            "file_path": file_path,
            "storage_backend": "local",
            "bucket": None,
            "blob_name": None,
        }

    def download(self, file_path: str) -> bytes:
        """Read and return file contents from local storage."""
        with open(file_path, "rb") as f:
            return f.read()

    def delete(self, file_path: str) -> bool:
        """Delete a file from local storage."""
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class GCSStorage(StorageAdapter):
    """
    Google Cloud Storage backend.
    Used in production mode with real GCP credentials.

    This implementation uses google-cloud-storage library to:
    - Upload documents to region-specific GCS buckets
    - Support multi-region and dual-region bucket configurations
    - Enable cost-aware and carbon-aware storage placement
    """

    def __init__(self):
        try:
            from google.cloud import storage
            self.client = storage.Client()
            self.bucket_name = GCS_BUCKET_NAME
            logger.info(f"GCSStorage initialized with bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def upload(self, file_data: bytes, file_name: str, region: str) -> dict:
        """
        Upload a file to GCS in the specified region.
        The region parameter controls which GCS bucket/location is used,
        enabling cost-aware and carbon-aware storage selection.
        """
        from google.cloud import storage

        # In production, different buckets would be created per region
        # For demo, we use a single bucket but store region in metadata
        bucket = self.client.bucket(self.bucket_name)
        blob_name = f"{region}/{file_name}"
        blob = bucket.blob(blob_name)

        # Set custom metadata with region and mode
        blob.metadata = {
            "storage_region": region,
            "content_type": "application/octet-stream",
        }

        blob.upload_from_string(file_data)

        logger.info(f"File '{file_name}' uploaded to GCS bucket '{self.bucket_name}' in region: {region}")
        return {
            "file_path": f"gs://{self.bucket_name}/{blob_name}",
            "storage_backend": "gcs",
            "bucket": self.bucket_name,
            "blob_name": blob_name,
        }

    def download(self, blob_name: str) -> bytes:
        """Download a file from GCS."""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()

    def delete(self, blob_name: str) -> bool:
        """Delete a file from GCS."""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True


def get_storage() -> StorageAdapter:
    """
    Factory function to return the configured storage backend.
    Defaults to local storage for development; switches to GCS when
    STORAGE_BACKEND=gcs and credentials are available.
    """
    if STORAGE_BACKEND == "gcs":
        try:
            return GCSStorage()
        except Exception as e:
            logger.warning(f"GCS initialization failed, falling back to local: {e}")
            return LocalStorage()
    return LocalStorage()
