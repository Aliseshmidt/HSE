import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Union
from transformers import AutoTokenizer
import onnxruntime as ort
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ONNX Embedding Service")

MODEL_PATH = "./onnx_model"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
session = ort.InferenceSession(f"{MODEL_PATH}/model.onnx")

input_names = [i.name for i in session.get_inputs()]
output_names = [o.name for o in session.get_outputs()]
logger.info(f"Model loaded. Inputs: {input_names}, Outputs: {output_names}")

class EmbedRequest(BaseModel):
    text: Union[str, List[str]] = Field(..., description="Один текст или список текстов")

def mean_pooling(last_hidden_state, attention_mask):
    if last_hidden_state.ndim == 2:
        return last_hidden_state
    mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
    mask_expanded = np.broadcast_to(mask_expanded, last_hidden_state.shape)
    sum_emb = np.sum(last_hidden_state * mask_expanded, axis=1)
    sum_mask = np.sum(mask_expanded, axis=1)
    sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
    return sum_emb / sum_mask

def embed_texts(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="np")
    if "token_type_ids" in inputs:
        del inputs["token_type_ids"]

    ort_inputs = {name: inputs[name] for name in input_names if name in inputs}
    ort_outputs = session.run(output_names, ort_inputs)

    if "last_hidden_state" in output_names:
        idx = output_names.index("last_hidden_state")
    else:
        idx = 0
    last_hidden_state = ort_outputs[idx]

    embeddings = mean_pooling(last_hidden_state, inputs["attention_mask"])
    return embeddings.tolist()

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
    uvicorn.run(app, host="0.0.0.0", port=8001)