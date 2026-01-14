import os
from pathlib import Path
from storage.supabase_client import supabase
from storage3.utils import StorageException

BUCKET = os.getenv("SUPABASE_BUCKET", "videos")


def upload_file(local_path: str, remote_path: str) -> str:
    """
    Upload a file to Supabase Storage and return its public URL.
    If the file already exists, delete it first to avoid duplicates.
    Handles race conditions gracefully.
    """
    bucket = supabase.storage.from_(BUCKET)
    remote_dir = str(Path(remote_path).parent)
    remote_name = str(Path(remote_path).name)

    try:
        existing_files = bucket.list(remote_dir) or []

        # Delete if exists
        if any(f.get("name") == remote_name for f in existing_files):
            try:
                bucket.remove([remote_path])
            except StorageException as e:
                # Ignore 404 if another worker removed it
                if e.args[0].get("statusCode") != 404:
                    raise

        # Upload the file
        with open(local_path, "rb") as f:
            bucket.upload(remote_path, f, file_options={"content-type": "application/octet-stream"})

    except StorageException as e:
        # Handle duplicate caused by race condition
        if e.args[0].get("statusCode") == 409:
            print(f"⚠️ File already exists, skipping upload: {remote_path}")
        else:
            raise

    return bucket.get_public_url(remote_path)
