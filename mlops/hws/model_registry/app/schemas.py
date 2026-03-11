from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    author: str

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class Model(ModelBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class VersionBase(BaseModel):
    version: str
    metrics: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    dataset: Dict[str, Any] = {}
    created_by: str

class VersionCreate(VersionBase):
    pass

class VersionUpdateStage(BaseModel):
    stage: str

class Version(VersionBase):
    id: UUID
    model_id: UUID
    stage: str
    artifact_path: str
    created_at: datetime

    class Config:
        orm_mode = True