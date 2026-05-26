from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.core.config import settings
from app.models.schemas import DetectedComponent
import requests, base64, json, os, re

router = APIRouter()

class VLMRequest(BaseModel):
    image_path: str
    components: List[DetectedComponent]

def build_prompt(components: List[DetectedComponent]) -> str:
    comp_list = "\n".join(
        [f"- {c.id}（{c.type}），位置：{c.bbox}" for c in components]
    )
    return f"""你是電路分析專家。圖片中已偵測到以下組件：

{comp_list}

請根據圖片中的實際接線，輸出組件之間的連接關係。
只輸出 JSON，不要有其他文字：

{{
  "relations": [
    {{"subject": "組件ID", "relation": "連接到", "object": "組件ID或GND或VCC"}},
    ...
  ]
}}
"""

@router.post("/extract")
async def extract_triples(req: VLMRequest):
    if not os.path.exists(req.image_path):
        raise HTTPException(404, f"找不到圖片：{req.image_path}")

    unconfirmed = [c.id for c in req.components if not c.confirmed]
    if unconfirmed:
        raise HTTPException(400, f"以下組件尚未確認：{unconfirmed}，請先在前端確認")

    with open(req.image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    prompt = build_prompt(req.components)
    try:
        resp = requests.post(
            f"{settings.lm_studio_url}/chat/completions",
            json={
                "model": settings.vlm_model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }],
                "max_tokens": 1000,
                "temperature": 0.1,
            },
            timeout=60
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(503, f"LM Studio 連線失敗：{e}")

    raw = resp.json()["choices"][0]["message"]["content"]

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise HTTPException(500, f"VLM 輸出格式錯誤：{raw}")

    try:
        relations_data = json.loads(match.group())
    except json.JSONDecodeError:
        raise HTTPException(500, f"JSON 解析失敗：{raw}")

    return {
        "components": [c.model_dump() for c in req.components],
        "relations": relations_data.get("relations", []),
        "raw_vlm_output": raw,
    }
