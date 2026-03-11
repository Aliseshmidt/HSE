from sqlalchemy.orm import Session
from . import models, schemas
from uuid import UUID

def create_model(db: Session, model: schemas.ModelCreate):
    db_model = models.Model(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_model(db: Session, model_id: UUID):
    return db.query(models.Model).filter(models.Model.id == model_id).first()

def get_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Model).offset(skip).limit(limit).all()

def create_version(db: Session, model_id: UUID, version: schemas.VersionCreate, artifact_path: str):
    db_version = models.ModelVersion(**version.dict(), model_id=model_id, artifact_path=artifact_path)
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def get_versions(db: Session, model_id: UUID, stage: str = None):
    query = db.query(models.ModelVersion).filter(models.ModelVersion.model_id == model_id)
    if stage:
        query = query.filter(models.ModelVersion.stage == stage)
    return query.all()

def update_version_stage(db: Session, version_id: UUID, stage: str):
    db_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()
    if db_version:
        db_version.stage = stage
        db.commit()
        db.refresh(db_version)
    return db_version