from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.db import SessionLocal
from typing import List
from uuid import UUID
import shutil
from app import storage
from app import models as db_models

router = APIRouter(prefix="/models", tags=["models"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Model, status_code=status.HTTP_201_CREATED)
def create_model(model: schemas.ModelCreate, db: Session = Depends(get_db)):
    return crud.create_model(db=db, model=model)

@router.get("/", response_model=List[schemas.Model])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_models(db, skip=skip, limit=limit)

@router.get("/{model_id}", response_model=schemas.Model)
def get_model(model_id: UUID, db: Session = Depends(get_db)):
    db_model = crud.get_model(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: UUID, db: Session = Depends(get_db)):
    model = crud.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    versions = db.query(db_models.ModelVersion).filter(
        db_models.ModelVersion.model_id == model_id
    ).all()

    for version in versions:
        storage.delete_model_files(model_id, version.version)

    for version in versions:
        db.delete(version)

    db.delete(model)
    db.commit()

    return None