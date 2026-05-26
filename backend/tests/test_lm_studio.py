"""
測試 LM Studio 連線
用法：python -m pytest backend/tests/test_lm_studio.py -v
或直接：python backend/tests/test_lm_studio.py
"""
import requests

BASE_URL = "http://localhost:1234/v1"

def test_text_model():
    """測試 phi4 純文字"""
    resp = requests.post(f"{BASE_URL}/chat/completions", json={
        "model": "phi-4-14b",
        "messages": [{"role": "user", "content": "回覆OK兩個字就好"}],
        "max_tokens": 10,
    })
    assert resp.status_code == 200, f"失敗：{resp.text}"
    print("✅ phi4 文字模型 OK")
    print("   回覆：", resp.json()["choices"][0]["message"]["content"])

def test_vlm_model():
    """測試 gemma3 視覺（純文字模式，不帶圖）"""
    resp = requests.post(f"{BASE_URL}/chat/completions", json={
        "model": "gemma-3-12b",
        "messages": [{"role": "user", "content": "回覆OK兩個字就好"}],
        "max_tokens": 10,
    })
    assert resp.status_code == 200, f"失敗：{resp.text}"
    print("✅ gemma3 VLM 模型 OK")
    print("   回覆：", resp.json()["choices"][0]["message"]["content"])

if __name__ == "__main__":
    print("測試 LM Studio 連線...")
    test_text_model()
    test_vlm_model()
    print("\n全部通過！")
