"""
進階技術指標與訊號分析模組 (RSI, MACD)
利用 `yfinance` 取得歷史價格並使用 `ta` 套件計算技術指標，產出超買或超賣等交易訊號。
"""

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD

def analyze_asset(yf_ticker_symbol: str) -> dict[str, any]:
    """
    分析單一資產的 RSI 與 MACD 狀態。
    
    Args:
        yf_ticker_symbol: 適用於 yfinance 的代號 (例如 "AAPL", "BTC-USD")
        
    Returns:
        包含指標數據與訊號的字典
    """
    try:
        # 取得過去 60 天的歷史資料來計算指標
        ticker = yf.Ticker(yf_ticker_symbol)
        df = ticker.history(period="60d")
        
        if df.empty or len(df) < 30:
            return {"rsi": None, "macd": None, "signal": None}
            
        # 計算 RSI (期數 14)
        rsi_indicator = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi_indicator.rsi()
        
        # 計算 MACD
        macd_indicator = MACD(close=df['Close'])
        df['MACD'] = macd_indicator.macd()
        df['MACD_Signal'] = macd_indicator.macd_signal()
        df['MACD_Hist'] = macd_indicator.macd_diff()
        
        # 取得最新一筆資料
        latest = df.iloc[-1]
        
        rsi_value = round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else None
        macd_val = round(latest['MACD'], 2) if not pd.isna(latest['MACD']) else None
        macd_hist = round(latest['MACD_Hist'], 2) if not pd.isna(latest['MACD_Hist']) else None
        
        # 產生訊號邏輯
        signal = None
        if rsi_value is not None:
            if rsi_value > 70:
                signal = "超買 (RSI > 70)"
            elif rsi_value < 30:
                signal = "超賣 (RSI < 30)"
        
        return {
            "rsi": rsi_value,
            "macd": macd_val,
            "macd_hist": macd_hist,
            "signal": signal
        }
    except Exception as e:
        print(f"⚠️ 分析 {yf_ticker_symbol} 時發生錯誤: {e}")
        return {"rsi": None, "macd": None, "signal": None}

def get_ta_signals(crypto_dict: dict, stock_dict: dict) -> dict[str, dict]:
    """
    對傳入的加密貨幣與股票字典進行技術分析
    """
    signals = {}
    
    # 針對加密貨幣 (轉換為 yfinance 格式，例如 btc -> BTC-USD)
    for symbol, data in crypto_dict.items():
        yf_symbol = f"{symbol.upper()}-USD"
        res = analyze_asset(yf_symbol)
        if res["signal"]:
            signals[symbol.upper()] = res
            
    # 針對美股 ETF
    for symbol, data in stock_dict.items():
        res = analyze_asset(symbol.upper())
        if res["signal"]:
            signals[symbol.upper()] = res
            
    return signals

if __name__ == "__main__":
    # 簡單測試
    print(analyze_asset("BTC-USD"))
    print(analyze_asset("SMH"))
