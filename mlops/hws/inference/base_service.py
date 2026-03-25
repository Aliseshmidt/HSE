"""
Эндпоинт: POST /embed
Ожидает JSON: {"text": "текст"} или {"texts": ["текст1", "текст2"]}
Возвращает эмбеддинги (list of lists).
"""
import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Base Embedding Service (PyTorch)")

MODEL_NAME = "sergeyzh/rubert-mini-frida"
DEVICE = "cpu"

# Загрузка модели и токенизатора
logger.info(f"Loading model {MODEL_NAME} on {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.to(DEVICE)
model.eval()
logger.info("Model loaded.")

class EmbedRequest(BaseModel):
    text: Union[str, List[str]] = Field(..., description="Один текст или список текстов")

def mean_pooling(last_hidden_state, attention_mask):
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
    sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
    return sum_embeddings / sum_mask

def embed_texts(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = mean_pooling(outputs.last_hidden_state, inputs["attention_mask"])
    return embeddings.cpu().numpy().tolist()

@app.post("/embed")
async def embed(request: EmbedRequest):
    try:
        if isinstance(request.text, str):
            texts = [request.text]
        else:
            texts = request.text
        if not texts:
            raise HTTPException(status_code=400, detail="Empty text list")
        embeddings = embed_texts(texts)
        if isinstance(request.text, str):
            embeddings = embeddings[0]
        return {"embeddings": embeddings}
    except Exception as e:
        logger.exception("Error during embedding")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)