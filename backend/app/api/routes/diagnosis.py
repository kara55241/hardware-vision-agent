from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.core.config import settings
from app.models.schemas import ComponentBase, Relation
import requests

router = APIRouter()

class DiagnosisRequest(BaseModel):
    components: List[ComponentBase]
    relations: List[Relation]

def build_diagnosis_prompt(components, relations) -> str:
    comp_str = ", ".join([f"{c.id}({c.type})" for c in components])
    rel_str = "\n".join([f"  {r.subject} --{r.relation}--> {r.object}" for r in relations])

    return f"""你是電路診斷專家。請分析以下電路接線是否正確，找出潛在問題。

組件：{comp_str}

接線關係：
{rel_str}

請輸出：
1. 整體狀態（正常 / 警告 / 錯誤）
2. 發現的問題清單（如果有）
3. 診斷說明

用繁體中文回答，簡潔明瞭。"""

@router.post("/analyze")
async def analyze(req: DiagnosisRequest):
    prompt = build_diagnosis_prompt(req.components, req.relations)

    try:
        resp = requests.post(
            f"{settings.lm_studio_url}/chat/completions",
            json={
                "model": settings.text_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=60
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(503, f"LM Studio 連線失敗：{e}")

    answer = resp.json()["choices"][0]["message"]["content"]

    status = "正常"
    if "錯誤" in answer or "危險" in answer or "短路" in answer:
        status = "錯誤"
    elif "警告" in answer or "注意" in answer or "建議" in answer:
        status = "警告"

    return {
        "status": status,
        "warnings": [],
        "explanation": answer,
    }
