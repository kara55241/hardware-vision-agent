"""
快速測試 YOLO 是否能跑
用法：python yolo/scripts/test_yolo.py --image path/to/circuit.jpg
"""
import argparse
from ultralytics import YOLO

def test(image_path: str, model_path: str = "yolov8n.pt"):
    model = YOLO(model_path)  # 先用預訓練，之後換成自訓練的 best.pt
    results = model(image_path)
    for r in results:
        print("偵測到的物件：")
        for box in r.boxes:
            print(f"  類別={r.names[int(box.cls)]}, 信心度={float(box.conf):.2f}, bbox={box.xyxy[0].tolist()}")
    results[0].save("output_test.jpg")
    print("結果已存為 output_test.jpg")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    args = parser.parse_args()
    test(args.image, args.model)
