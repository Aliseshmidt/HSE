from fastapi import FastAPI
from .api import models, versions
from .db import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Model Registry API")

app.include_router(models.router)
app.include_router(versions.router)

@app.get("/")
def root():
    return {"message": "Model Registry is running"}