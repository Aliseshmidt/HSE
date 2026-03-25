import asyncio
import time
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Union
from contextlib import asynccontextmanager
from transformers import AutoTokenizer
import onnxruntime as ort
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = "./onnx_model"
MAX_BATCH_SIZE = 32
BATCH_TIMEOUT = 0.05


tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
session = ort.InferenceSession(f"{MODEL_PATH}/model.onnx")
input_names = [i.name for i in session.get_inputs()]
output_names = [o.name for o in session.get_outputs()]
logger.info(f"Model loaded. Inputs: {input_names}, Outputs: {output_names}")

queue = None
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue, worker_task
    queue = asyncio.Queue()
    worker_task = asyncio.create_task(worker())
    logger.info("Dynamic batching worker started.")
    yield
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    logger.info("Worker stopped.")

app = FastAPI(title="Dynamic Batching Embedding Service", lifespan=lifespan)

def mean_pooling(last_hidden_state: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    if last_hidden_state.ndim == 2:
        return last_hidden_state
    mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
    mask_expanded = np.broadcast_to(mask_expanded, last_hidden_state.shape)
    sum_emb = np.sum(last_hidden_state * mask_expanded, axis=1)
    sum_mask = np.sum(mask_expanded, axis=1)
    sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
    return sum_emb / sum_mask

async def process_batch(batch_items: List[tuple]):
    texts = [text for _, text in batch_items]
    try:
        logger.info(f"Processing batch of {len(texts)} texts")
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
        for (future, _), emb in zip(batch_items, embeddings):
            future.set_result(emb.tolist())
        logger.info("Batch processed successfully")
    except Exception as e:
        logger.exception("Batch processing failed")
        for future, _ in batch_items:
            future.set_exception(e)

async def worker():
    global queue
    logger.info("Worker started")
    while True:
        batch_items = []
        try:
            first = await queue.get()
            batch_items.append(first)
        except asyncio.CancelledError:
            break

        start_time = time.perf_counter()
        while len(batch_items) < MAX_BATCH_SIZE:
            remaining_time = BATCH_TIMEOUT - (time.perf_counter() - start_time)
            if remaining_time <= 0:
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=remaining_time)
                batch_items.append(item)
            except asyncio.TimeoutError:
                break

        asyncio.create_task(process_batch(batch_items))

class EmbedRequest(BaseModel):
    text: Union[str, List[str]] = Field(..., description="Один текст или список текстов")

@app.post("/embed")
async def embed(request: EmbedRequest):
    global queue
    if queue is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    if isinstance(request.text, str):
        texts = [request.text]
    else:
        texts = request.text

    if not texts:
        raise HTTPException(status_code=400, detail="Empty text list")

    loop = asyncio.get_event_loop()
    futures = [loop.create_future() for _ in texts]

    for text, fut in zip(texts, futures):
        await queue.put((fut, text))

    try:
        results = await asyncio.gather(*futures)
    except Exception as e:
        logger.exception("Error gathering results")
        raise HTTPException(status_code=500, detail=str(e))

    if isinstance(request.text, str):
        results = results[0]

    return {"embeddings": results}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)