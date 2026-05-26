# 硬體視覺診斷助手

基於多模態 GraphRAG 的電路診斷系統。使用者上傳電路照片，系統自動辨識組件、提取接線關係、比對標準電路，輸出診斷警告。

## 技術棧

| 層級 | 技術 |
|------|------|
| 物件偵測 | YOLOv8 |
| VLM 看圖 | gemma3:12b（透過 LM Studio） |
| 文字推理 | phi4:14b（透過 LM Studio） |
| 後端 | FastAPI + Python 3.12 |
| 圖資料庫 | Neo4j |
| 向量檢索 | ChromaDB |
| 前端 | HTML/CSS/JS（規劃遷移 Vue 3） |

## 系統流程

```
上傳圖片 → YOLO 偵測組件 → Human-in-the-loop 確認
        → VLM 提取接線關係 → Neo4j 建圖 → phi4 診斷輸出
```

## 環境需求

- Python 3.12
- [LM Studio](https://lmstudio.ai/)（需載入 gemma3:12b 和 phi4:14b）
- [Neo4j Desktop](https://neo4j.com/download/)
- Apple M5 / macOS 26（開發環境）

## 快速開始

### 1. 啟動 LM Studio
載入以下兩個模型並啟動 Local Server（預設 port 1234）：
- `gemma3:12b`（VLM）
- `phi4:14b`（文字推理）

### 2. 啟動 Neo4j Desktop
打開 Neo4j Desktop，啟動資料庫（RUNNING 狀態）。

### 3. 設定環境變數
```bash
cp backend/.env.example backend/.env  # 若有 .env.example
# 或直接編輯 backend/.env，填入 Neo4j 密碼
```

### 4. 啟動後端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

確認 API 運行：打開 http://localhost:8000，應看到 `{"status":"ok"}`

### 5. 打開前端
用瀏覽器開啟 `frontend/index.html`，或使用 VS Code Live Server。

### 6. 測試連線
```bash
# 測試 LM Studio
python backend/tests/test_lm_studio.py

# 測試 YOLO
python yolo/scripts/test_yolo.py --image your_circuit.jpg
```

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/detect/` | POST | 上傳圖片，YOLO 偵測組件 |
| `/api/vlm/extract` | POST | 組件 + 圖片 → VLM 提取接線關係 |
| `/api/graph/save` | POST | 三元組寫入 Neo4j |
| `/api/graph/query/{image_id}` | GET | 查詢圖譜資料 |
| `/api/diagnosis/analyze` | POST | 三元組 → phi4 診斷分析 |

完整 API 文件：http://localhost:8000/docs

## 三元組輸出格式

```json
{
  "components": [
    {"id": "R1", "type": "resistor", "bbox": [x1, y1, x2, y2], "confirmed": true}
  ],
  "relations": [
    {"subject": "R1", "relation": "連接到", "object": "LED1"}
  ]
}
```

## 資料夾結構

```
hardware-vision-diag/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # detect, vlm, graph, diagnosis
│   │   ├── core/           # config.py（settings）
│   │   └── models/         # schemas.py
│   ├── tests/              # test_lm_studio.py
│   ├── data/
│   │   ├── uploads/        # 上傳的圖片
│   │   ├── yolo_models/    # 放 best.pt
│   │   └── chromadb/       # 向量資料庫
│   ├── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── index.html          # 主要前端介面
├── yolo/
│   ├── datasets/
│   │   ├── images/train、val/
│   │   └── labels/train、val/
│   └── scripts/
│       └── test_yolo.py
└── TODO.md
```

## 注意事項

- YOLO 必須先偵測組件（提供 Bounding Box），再送 VLM，避免幻覺
- Human-in-the-loop：YOLO 結果需使用者確認才進入下一步
- 全本地端執行，不使用任何雲端 API（比賽需求）
- Ollama 與 M5/macOS 26 不相容，請使用 LM Studio
