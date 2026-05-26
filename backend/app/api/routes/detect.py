from fastapi import APIRouter, UploadFile, File, HTTPException
from ultralytics import YOLO
from PIL import Image
from app.core.config import settings
import io, os, uuid

router = APIRouter()

_model = None

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CLASS_PREFIX = {
    "resistor": "R",
    "capacitor": "C",
    "led": "LED",
    "transistor": "Q",
    "inductor": "L",
    "diode": "D",
    "ic": "U",
}

def get_model():
    global _model
    if _model is None:
        _model = YOLO(settings.yolo_model_path)
    return _model

def make_comp_id(cls_name: str, count: int) -> str:
    prefix = CLASS_PREFIX.get(cls_name.lower(), cls_name[:2].upper())
    return f"{prefix}{count}"

@router.post("/")
async def detect(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "請上傳圖片檔案")

    image_id = str(uuid.uuid4())[:8]
    filename = f"{image_id}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    image.save(save_path)

    results = get_model()(image, conf=0.25)
    boxes = results[0].boxes
    names = results[0].names

    components = []
    counter = {}

    for box in boxes:
        cls_name = names[int(box.cls)]
        counter[cls_name] = counter.get(cls_name, 0) + 1
        comp_id = make_comp_id(cls_name, counter[cls_name])

        components.append({
            "id": comp_id,
            "type": cls_name,
            "bbox": [round(v, 2) for v in box.xyxy[0].tolist()],
            "confidence": round(float(box.conf), 3),
            "confirmed": False,
        })

    return {
        "image_id": image_id,
        "image_path": save_path,
        "components": components,
        "total": len(components),
    }
