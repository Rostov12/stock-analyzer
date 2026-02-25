import os
import json
from google import genai
from google.genai import types

def parse_transaction_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[dict | None, str | None]:
    """
    使用 Gemini Vision 模型解析交易明細截圖，萃取交易資料。
    
    Args:
        image_bytes: 圖片的二進位資料。
        mime_type: 圖片類型，預設為 image/jpeg。
        
    Returns:
        (JSON_Dict, 錯誤訊息)。若成功，錯誤訊息為 None；若失敗，JSON_Dict 為 None。
        格式範例:
        {
            "symbol": "URNM",
            "transaction_type": "BUY",
            "price": 69.35,
            "quantity": 20.0,
            "timestamp": "2026/02/04"
        }
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ 錯誤: 找不到 GEMINI_API_KEY 環境變數。")
        return None, "找不到 GEMINI_API_KEY 環境變數。請確認已設定環境變數。"
        
    client = genai.Client(api_key=api_key)
    
    prompt = """
    這是一張券商APP(如口袋證券)的成交紀錄明細截圖。
    請仔細閱讀圖片中的詳細資料，並從中提取出以下資訊，嚴格以 JSON 格式回傳。
    
    JSON 格式定義：
    {
        "symbol": "交易標的代號 (例如 URNM, NLR。請以英文大寫表示)",
        "transaction_type": "BUY 或是 SELL (對應畫面中的「買進」或「賣出」)",
        "price": 成交單價 (請回傳純數字，例如 69.35，去除「元」或「$」等符號),
        "quantity": 成交數量 (請回傳純數字，例如 20，去除「股」等單位),
        "timestamp": "成交日期與時間 (優先尋找「成交時間」，格式轉換為 YYYY-MM-DD 或 YYYY/MM/DD)"
    }
    
    重要指示：
    1. 若畫面中文字顏色較淺或模糊，請根據上下文判斷。
    2. 如果有多筆資料，請抓取「展開詳細資訊」的那一筆 (通常包含委託書號、手續費、稅費等細節)。
    3. 只回傳 JSON 內容，不要包含 ```json 代碼塊或其他任何文字說明。
    4. 確保輸出是合法的 JSON。
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
        )
        
        text = response.text.strip()
        
        # 強大清理邏輯：移除任何可能存在的 Markdown 標籤或說明文字
        if "{" in text and "}" in text:
            start_index = text.find("{")
            end_index = text.rfind("}") + 1
            text = text[start_index:end_index]
            
        result = json.loads(text.strip())
        return result, None
        
    except json.JSONDecodeError as e:
        error_msg = f"AI 回傳了非 JSON 格式的內容: {response.text}"
        print(f"⚠️ 解析 JSON 失敗: {e}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Gemini API 處理過程中發生錯誤: {e}"
        print(f"⚠️ {error_msg}")
        # 如果是安全阻擋，這裡也可以捕捉
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            error_msg += f" (安全阻擋: {e.response.prompt_feedback})"
        return None, error_msg

# 測試用區塊
if __name__ == "__main__":
    # 若要本地測試，可在此處讀取某張圖片的 bytes 或設定環境變數
    print("此模組用於解析交易圖片。請至 telegram_bot.py 中整合呼叫。")
