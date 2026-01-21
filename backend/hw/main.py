from fastapi import FastAPI
from routers.predict import router as predict_router
import uvicorn

app = FastAPI()
app.include_router(predict_router)

@app.get("/")
async def root():
    return {'message': 'Hello World'}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
