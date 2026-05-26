# 待辦事項

## 進行中

- [ ] 前端：手動新增組件功能（YOLO 偵測不到時可手動輸入）
- [ ] 前端：NeoVis.js 電路圖譜視覺化
- [ ] 找 Roboflow 預訓練電路元件模型

---

## 待完成

### 前端
- [ ] 手動新增組件 UI（ID 輸入 + 類型下拉選單 + 刪除按鈕）
- [ ] NeoVis.js 整合（VLM 完成後自動渲染圖譜）
- [ ] VLM 完成後自動呼叫 `/api/graph/save` 儲存

### YOLO 訓練
- [ ] 建立 `yolo/data.yaml`（類別定義）
- [ ] 建立 `yolo/scripts/train.py`（M5 用 mps 加速）
- [ ] 建立 `yolo/scripts/validate.py`（mAP 評估）
- [ ] 收集電路組件圖片資料（目標：每類 200 張以上）
- [ ] 用 Roboflow 標注資料（支援多人協作、YOLO 格式匯出）
- [ ] 訓練自訂模型，產出 `best.pt`
- [ ] 替換 `detect.py` 模型路徑

### 預訓練模型（短期替代方案）
- [ ] Roboflow Universe 搜尋 `electronic-components` 或 `pcb-component-detection`
- [ ] 下載 `.pt` 放入 `backend/data/yolo_models/best.pt`
- [ ] 更新 `detect.py` 的 `CLASS_PREFIX` 對應新模型類別名稱

### ChromaDB 向量檢索（尚未接）
- [ ] 設計標準電路的向量表示
- [ ] 建立標準電路資料庫（正確接線的三元組）
- [ ] 診斷時從 ChromaDB 查詢最相似的標準電路做比對
- [ ] 接入 `/api/diagnosis/analyze` 流程

---

## 已完成

- [x] FastAPI 後端架構（detect / vlm / graph / diagnosis）
- [x] YOLO 偵測端點（支援圖片上傳、組件 ID 命名）
- [x] VLM 三元組提取（gemma3:12b via LM Studio）
- [x] Neo4j 圖譜寫入與查詢
- [x] phi4 診斷分析端點
- [x] 前端 5 步驟流程 UI
- [x] Human-in-the-loop 組件確認
- [x] Bounding Box Canvas 繪製
- [x] pydantic-settings 升級（Pydantic v2 相容）
- [x] YOLO 懶載入（避免啟動時崩潰）
- [x] 組件 ID 命名修正（R1, LED1 而非 RE1, LE1）
- [x] Neo4j 連線設定修正（neo4j:// 協定）
- [x] 前端 XSS 修正（textContent 取代 innerHTML）
- [x] JSON 回應 UTF-8 編碼修正

---

## 已知問題

| 問題 | 嚴重度 | 說明 |
|------|--------|------|
| yolov8n.pt 無法偵測電路組件 | 高 | 通用模型，需替換預訓練或自訓練模型 |
| ChromaDB 完全未使用 | 中 | 已安裝但未接入任何流程 |
| Neo4j driver 每次請求重建 | 低 | 可加 connection pool 優化 |
| 前端刷新後資料遺失 | 低 | 無持久化，demo 用途可接受 |
