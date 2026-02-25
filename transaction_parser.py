import os
import json
import google.generativeai as genai

def parse_transaction_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict | None:
    """
    使用 Gemini Vision 模型解析交易明細截圖，萃取交易資料。
    
    Args:
        image_bytes: 圖片的二進位資料。
        mime_type: 圖片類型，預設為 image/jpeg。
        
    Returns:
        解析成功的 JSON 字典，若失敗則回傳 None。
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
        return None
        
    genai.configure(api_key=api_key)
    
    # 選擇最新的輕量級多模態模型 (Gemini 1.5 Flash 或 2.5 Flash 提供高速視覺解析)
    # 我們這裡使用 gemini-1.5-flash 作為預設相容穩定版
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": image_bytes}
        ])
        
        text = response.text.strip()
        
        # 強大清理邏輯：移除任何可能存在的 Markdown 標籤或說明文字
        if "{" in text and "}" in text:
            start_index = text.find("{")
            end_index = text.rfind("}") + 1
            text = text[start_index:end_index]
            
        result = json.loads(text.strip())
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ 解析 JSON 失敗: {e}")
        print(f"原始回傳內容: {response.text}")
        return None
    except Exception as e:
        print(f"⚠️ Gemini API 呼叫失敗: {e}")
        return None

# 測試用區塊
if __name__ == "__main__":
    # 若要本地測試，可在此處讀取某張圖片的 bytes 或設定環境變數
    print("此模組用於解析交易圖片。請至 telegram_bot.py 中整合呼叫。")
