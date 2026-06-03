from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.api.routes import detect, vlm, graph, diagnosis, circuit
import json
import os

class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

app = FastAPI(
    title="硬體視覺診斷助手",
    version="0.2.0",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router,    prefix="/api/detect",    tags=["YOLO偵測"])
app.include_router(vlm.router,       prefix="/api/vlm",       tags=["VLM分析"])
app.include_router(graph.router,     prefix="/api/graph",     tags=["Neo4j圖譜"])
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["診斷推理"])
app.include_router(circuit.router,   prefix="/api/circuit",   tags=["電路組合"])

os.makedirs("data/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

@app.get("/")
def root():
    return {"status": "ok", "message": "硬體視覺診斷助手 API 運行中"}
