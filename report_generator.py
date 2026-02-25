import os
import json
from datetime import datetime
import pandas as pd
from google import genai

try:
    import yfinance as yf
except ImportError:
    yf = None

def get_market_data(tickers: list[str], period="5d") -> str:
    """從 yfinance 抓取所需標的歷史資料，轉化為摘要字串"""
    if yf is None:
        return "無法獲取市場即時資料，因為找不到 yfinance 模組。"
    
    summary_lines = []
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if not hist.empty and len(hist) >= 2:
                current_price = float(hist["Close"].iloc[-1])
                prev_price = float(hist["Close"].iloc[-2])
                change_pct = (current_price - prev_price) / prev_price * 100
                summary_lines.append(f"{ticker}: 最新收盤/現價 ${current_price:.2f} (單日變化 {change_pct:+.2f}%)")
            else:
                summary_lines.append(f"{ticker}: 無法取得最近兩日數據。")
        except Exception as e:
            summary_lines.append(f"{ticker}: 抓取失敗 ({e})")
            
    return "\n".join(summary_lines)

def call_gemini(prompt: str, context: str) -> str:
    """呼叫 Gemini 模型產生報告"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ 錯誤: 找不到 GEMINI_API_KEY 環境變數。請在 Zeabur 設定金鑰。"
        
    try:
        client = genai.Client(api_key=api_key)
        
        full_prompt = f"""
{prompt}

=== 以下是今天最新的市場數據 (由背景 Python yfinance 即時抓取) ===
{context}

請基於上述資料與專業分析師的人設，寫出完整的 Markdown 報告。
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        error_msg = f"Gemini API 處理失敗: {e}"
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            error_msg += f" (被安全機制阻擋: {e.response.prompt_feedback})"
        return error_msg

def generate_us_intraday_report() -> str:
    tickers = ["^DJI", "^GSPC", "^IXIC", "NVDA", "TSLA", "SMH", "QQQ"]
    market_data = get_market_data(tickers, period="2d")
    
    prompt = """
    你是一位華爾街資深分析師。現在是美股盤中時間。
    請撰寫一份「美股盤中即時分析報告」。
    
    報告必須包含以下區塊：
    1. 盤中大盤總結 (三大指數表現、市場情緒是貪婪還是恐懼)
    2. 焦點板塊掃描 (比如半導體、AI、電動車等目前的趨勢)
    3. 下半場重點關注 (提醒投資者留意什麼支撐/壓力位或可能出現的突發事件)
    
    排版規定：請使用豐富的 Markdown 標籤 (Header, 粗體, 列表)，並加入合適的 Emoji 增加閱讀體驗。
    """
    
    return call_gemini(prompt, market_data)

def generate_us_close_report() -> str:
    tickers = ["^DJI", "^GSPC", "^IXIC", "NVDA", "TSLA", "SMH", "QQQ"]
    market_data = get_market_data(tickers, period="2d")
    
    prompt = """
    你是一位華爾街頂尖的資深市場策略師。現在美股已經收盤。
    請撰寫一份「美股盤後總結與明日展望報告」。
    
    報告必須包含以下區塊：
    1. 收盤定調 (市場今天是多頭勝利、空頭屠殺，還是震盪洗盤？)
    2. 三大指數與核心資產成績單 (DJI, S&P500, Nasdaq，以及科技巨頭表現評析)
    3. 資金流向與板塊輪動 (資金今天跑到哪裡去了？哪些板塊遭拋售？)
    4. 明日操作建議與風險提示 (做多或做空？還是觀望？給出明確的行動指南)
    
    排版規定：請展現你專業、果斷的文筆。使用 Markdown 標籤以條理分明呈現，加入適當的 Emoji。
    """
    
    return call_gemini(prompt, market_data)

def generate_uranium_report() -> str:
    # 針對鈾礦/核能/原物料相關的 ETF
    tickers = ["URNM", "NLR", "GLD", "CPER", "URA", "CCJ"]
    market_data = get_market_data(tickers, period="5d")
    
    prompt = """
    你是一位專攻「全球能源轉型與原物料」的頂尖研究員 (同時熟悉地緣政治)。現在需要產出一份「每週鈾礦與核能 ETF 專題分析」。
    
    報告必須包含以下區塊：
    1. 鈾礦與核能板塊一週回顧 (綜合評定 URNM, NLR 等標的的表現，是突破還是回調？)
    2. 驅 হত্যার要素分析 (例如：各國重啟核能政策、AI 耗電導致核電復興、地緣政治對鈾供應鏈的干擾)
    3. 相關原物料連動 (比較黃金 GLD 避險情緒與銅 CPER 工業需求的走向，它們與核能板塊的資金有沒有排擠效應？)
    4. 投資佈局建議 (給出針對中長線投資人的建倉、減碼或是持有的建議)
    
    排版規定：由於是深度專題，請寫得鉅細靡遺、文筆專業流暢，使用 Markdown 並且條理清晰，加入適當 Emoji。
    """
    
    return call_gemini(prompt, market_data)

def send_telegram_report(text: str) -> str:
    import requests
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '8589611809:AAGpQAQ3usjx8_9XTOKvpuEW9TkrMZYiwXU')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '6536967026') # 預設為使用者之前常用的 Chat ID
    
    if not bot_token or not chat_id:
        return "⚠️ 未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID。"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML" # 因應 Telegram Markdown 嚴格限制，改回純文字或HTML較穩定，這裡選用不帶 parse_mode 或簡單的。我們這裡先不用parse_mode以免出錯。
    }
    if payload["parse_mode"]:
        del payload["parse_mode"]
        
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            return "✅ 報告已成功推送至您的 Telegram！"
        else:
            return f"❌ 推送失敗: {res.text}"
    except Exception as e:
        return f"❌ 網路連線錯誤: {e}"

if __name__ == "__main__":
    print(generate_us_close_report())
