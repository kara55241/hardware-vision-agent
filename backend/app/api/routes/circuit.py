from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.models.schemas import DetectedComponent, Connection
from pydantic import BaseModel
from typing import List
import requests

router = APIRouter()

STANDARD_LED_CIRCUIT = {
    "name": "LED限流電路",
    "required_types": ["resistor", "led"],
    "resistor_range": (100, 1000),
}

class BuildRequest(BaseModel):
    image_id: str
    components: List[DetectedComponent]
    connections: List[Connection]
    power_type: str

def validate_circuit(components: List[DetectedComponent], connections: List[Connection]) -> dict:
    types = [c.type.lower() for c in components]
    has_resistor = any("resistor" in t for t in types)
    has_led = any("led" in t for t in types)

    resistor_value_ok = True
    for c in components:
        if "resistor" in c.type.lower() and c.value:
            try:
                val = float(c.value)
                lo, hi = STANDARD_LED_CIRCUIT["resistor_range"]
                if not (lo <= val <= hi):
                    resistor_value_ok = False
            except ValueError:
                pass

    conn_nodes = {conn.from_node.lower() for conn in connections} | {conn.to_node.lower() for conn in connections}
    has_gnd = any("gnd" in n or "ground" in n for n in conn_nodes)

    return {
        "has_resistor": has_resistor,
        "has_led": has_led,
        "resistor_value_ok": resistor_value_ok,
        "has_gnd": has_gnd,
    }

def build_diagnosis_prompt(components: List[DetectedComponent], connections: List[Connection], power_type: str) -> str:
    comp_str = ", ".join([
        f"{c.id}({c.type}{', ' + c.value + c.unit if c.value else ''})"
        for c in components
    ])
    conn_str = "\n".join([f"  {c.from_node} → {c.to_node}" for c in connections])
    voltage = "5V" if power_type == "Arduino" else "電池電壓"

    return f"""你是一位親切的電路學習助手，幫助學生檢查麵包板電路。請用鼓勵的語氣分析以下電路。

電源：{power_type}（{voltage}）
組件：{comp_str}

連接關係：
{conn_str}

請依序回答（第一行必須是狀態標記）：

第一行：【正常】、【警告】或【錯誤】（只選一個）

接著說明：
1. 限流電阻是否合適（{voltage} 供電，LED 常見範圍 100Ω–1kΩ，220Ω 是標準值）
2. 連接順序是否正確（電源 → 電阻 → LED → GND）
3. 有沒有需要注意的地方

語氣正向，像老師給學生回饋，用繁體中文。"""

@router.post("/build")
async def build_circuit(req: BuildRequest):
    validation = validate_circuit(req.components, req.connections)

    circuit_data = {
        "image_id": req.image_id,
        "components": [c.model_dump() for c in req.components],
        "connections": [{"from": conn.from_node, "to": conn.to_node} for conn in req.connections],
        "power_type": req.power_type,
    }

    prompt = build_diagnosis_prompt(req.components, req.connections, req.power_type)
    try:
        resp = requests.post(
            f"{settings.lm_studio_url}/chat/completions",
            json={
                "model": settings.text_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(503, f"LM Studio 連線失敗：{e}")

    first_line = answer.split("\n")[0]
    if "【錯誤】" in first_line:
        status = "錯誤"
    elif "【警告】" in first_line:
        status = "警告"
    else:
        status = "正常"
    if status == "正常" and not validation["resistor_value_ok"]:
        status = "警告"

    return {
        "circuit_data": circuit_data,
        "validation": validation,
        "status": status,
        "explanation": answer,
    }
