from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from PIL import Image
from app.core.config import settings
from app.models.schemas import DetectedComponent
import requests, base64, json, os, re, io

router = APIRouter()

# ── 共用：圖片轉 base64 ────────────────────────────
def image_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def crop_to_b64(path: str, bbox: List[float], padding: int = 10) -> str:
    with Image.open(path) as img:
        x1, y1, x2, y2 = bbox
        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(img.width, int(x2) + padding)
        y2 = min(img.height, int(y2) + padding)
        cropped = img.crop((x1, y1, x2, y2)).convert("RGB")
    buf = io.BytesIO()
    cropped.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def parse_json_from_vlm(raw: str) -> dict | None:
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None

def call_vlm(image_b64: str, prompt: str) -> str:
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
                "max_tokens": 500,
                "temperature": 0.1,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(503, f"LM Studio 連線失敗：{e}")

# ── /quality-check ────────────────────────────────
class QualityCheckRequest(BaseModel):
    image_path: str

@router.post("/quality-check")
async def quality_check(req: QualityCheckRequest):
    if not os.path.exists(req.image_path):
        raise HTTPException(404, f"找不到圖片：{req.image_path}")

    image_b64 = image_to_b64(req.image_path)
    prompt = """請判斷這張圖片是否適合進行電路分析。
評估標準：
1. 圖片是否清晰（不模糊）
2. 是否能看到電子組件（電阻、LED 等）
3. 光線是否足夠

只輸出 JSON，不要其他文字：
{"passed": true/false, "feedback": "一句話說明原因"}"""

    raw = call_vlm(image_b64, prompt)
    result = parse_json_from_vlm(raw)
    if not result:
        return {"passed": True, "feedback": "無法判斷，預設通過"}
    return {"passed": bool(result.get("passed", True)), "feedback": result.get("feedback", "")}

# ── /color-band ───────────────────────────────────
class ColorBandRequest(BaseModel):
    image_path: str
    resistor_id: str
    bbox: List[float]

@router.post("/color-band")
async def read_color_band(req: ColorBandRequest):
    if not os.path.exists(req.image_path):
        raise HTTPException(404, f"找不到圖片：{req.image_path}")

    image_b64 = crop_to_b64(req.image_path, req.bbox)
    prompt = """這是一個電阻的特寫圖片。請識別色環顏色並計算電阻值。
只輸出 JSON，不要其他文字：
{"value": "220", "unit": "Ω", "bands": "紅紅棕"}

如果看不清楚色環，value 填 "unknown"。"""

    raw = call_vlm(image_b64, prompt)
    result = parse_json_from_vlm(raw)
    if not result:
        return {"resistor_id": req.resistor_id, "value": "unknown", "unit": "Ω"}
    return {
        "resistor_id": req.resistor_id,
        "value": result.get("value", "unknown"),
        "unit": result.get("unit", "Ω"),
    }

# ── /extract（原有，保留相容）────────────────────
class VLMRequest(BaseModel):
    image_path: str
    components: List[DetectedComponent]

def build_extract_prompt(components: List[DetectedComponent]) -> str:
    comp_list = "\n".join([f"- {c.id}（{c.type}），位置：{c.bbox}" for c in components])
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

    image_b64 = image_to_b64(req.image_path)
    raw = call_vlm(image_b64, build_extract_prompt(req.components))

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
