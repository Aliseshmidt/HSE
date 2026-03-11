import os
import shutil
from pathlib import Path
from uuid import UUID

STORAGE_ROOT = Path("./storage")

def ensure_storage():
    STORAGE_ROOT.mkdir(exist_ok=True)

def save_model_files(model_id: UUID, version: str, files: list) -> str:
    version_path = STORAGE_ROOT / str(model_id) / version
    version_path.mkdir(parents=True, exist_ok=True)
    for file in files:
        file_path = version_path / file.filename
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    return str(version_path)

def get_model_files_path(model_id: UUID, version: str) -> Path:
    return STORAGE_ROOT / str(model_id) / version

def delete_model_files(model_id: UUID, version: str):
    shutil.rmtree(STORAGE_ROOT / str(model_id) / version, ignore_errors=True)