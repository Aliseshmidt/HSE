from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app import crud, schemas, storage
from app.db import SessionLocal
from app import models
from typing import List, Optional
from uuid import UUID
import json
from fastapi.responses import FileResponse
import os
import zipfile
import tempfile

router = APIRouter(prefix="/models/{model_id}/versions", tags=["versions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Version, status_code=status.HTTP_201_CREATED)
async def create_version(
    model_id: UUID,
    metadata: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    model = crud.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        version_data = schemas.VersionCreate(**json.loads(metadata))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    storage.ensure_storage()
    artifact_path = storage.save_model_files(model_id, version_data.version, files)

    db_version = crud.create_version(db, model_id, version_data, artifact_path)
    return db_version

@router.get("/", response_model=List[schemas.Version])
def list_versions(model_id: UUID, stage: Optional[str] = None, db: Session = Depends(get_db)):
    model = crud.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return crud.get_versions(db, model_id, stage)

@router.put("/{version}/stage", response_model=schemas.Version)
def update_stage(model_id: UUID, version: str, stage_update: schemas.VersionUpdateStage, db: Session = Depends(get_db)):
    db_version = db.query(models.ModelVersion).filter(
        models.ModelVersion.model_id == model_id,
        models.ModelVersion.version == version
    ).first()
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    updated = crud.update_version_stage(db, db_version.id, stage_update.stage)
    return updated

@router.get("/{version}/download")
def download_version(model_id: UUID, version: str, db: Session = Depends(get_db)):
    db_version = db.query(models.ModelVersion).filter(
        models.ModelVersion.model_id == model_id,
        models.ModelVersion.version == version
    ).first()
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    path = Path(db_version.artifact_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifacts not found on disk")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, 'w') as z:
            for file in path.iterdir():
                z.write(file, arcname=file.name)
    return FileResponse(tmp.name, media_type="application/zip", filename=f"{model_id}_{version}.zip")