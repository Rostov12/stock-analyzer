"""
資產價格監控腳本
整合加密貨幣（BTC, ETH, SOL, ADA）和美股 ETF 數據，生成 JSON 報告並觸發警報。
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import requests

try:
    import yfinance as yf
except ImportError:
    yf = None  # type: ignore[assignment]

import database
import indicator_analyzer
# --- 加密貨幣配置 ---
COIN_MAP: dict[str, str] = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "solana": "sol",
}

COIN_NAMES: dict[str, str] = {
    "btc": "Bitcoin",
    "eth": "Ethereum",
    "sol": "Solana",
}

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# --- 美股 ETF 配置 ---
ETF_MAP: dict[str, str] = {
    "SMH": "半導體ETF",
    "AIQ": "人工智慧ETF",
    "BOTZ": "機器人ETF",
    "NLR": "核能ETF",
    "URNM": "鈾礦ETF",
    "GLD": "黃金ETF",
    "CPER": "銅ETF",
}


def fetch_crypto_prices() -> dict[str, Any]:
    """從 CoinGecko API 抓取加密貨幣價格。

    Returns:
        原始 API 響應數據。

    Raises:
        requests.RequestException: 當 API 請求失敗時。
    """
    params = {
        "ids": ",".join(COIN_MAP.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def process_crypto_prices(raw: dict[str, Any]) -> dict[str, Any]:
    """處理原始加密貨幣 API 數據，格式化為目標結構。

    Args:
        raw: CoinGecko API 返回的原始數據。

    Returns:
        格式化後的加密貨幣價格字典。
    """
    crypto: dict[str, Any] = {}
    for coin_id, symbol in COIN_MAP.items():
        data = raw.get(coin_id)
        if not data:
            print(f"⚠️  警告：API 未返回 {coin_id} 的數據，跳過")
            continue
        crypto[symbol] = {
            "type": "crypto",
            "name": COIN_NAMES.get(symbol, symbol.upper()),
            "usd": round(data.get("usd", 0), 2),
            "change_24h": round(data.get("usd_24h_change", 0), 2),
        }
    return crypto


def fetch_stock_prices() -> dict[str, Any]:
    """使用 yfinance 抓取美股 ETF 價格及 24 小時變化。

    Returns:
        格式化後的股票價格字典。
    """
    if yf is None:
        print("⚠️  警告：yfinance 未安裝，跳過股票數據")
        return {}
        
    stocks: dict[str, Any] = {}
    for ticker, name in ETF_MAP.items():
        try:
            t = yf.Ticker(ticker)
            # 使用 5d 確保在週末或假日也能取得足夠的交易日數據
            hist = t.history(period="5d")
            if hist.empty or len(hist) < 2:
                print(f"⚠️  警告：無法獲取 {ticker} 的歷史數據，跳過")
                continue
            current_price = round(float(hist["Close"].iloc[-1]), 2)
            prev_price = float(hist["Close"].iloc[-2])
            change_24h = round((current_price - prev_price) / prev_price * 100, 2)
            stocks[ticker.lower()] = {
                "type": "stock",
                "name": name,
                "usd": current_price,
                "change_24h": change_24h,
            }
        except Exception as e:
            print(f"⚠️  警告：獲取 {ticker} 數據失敗：{e}，跳過")
    return stocks


def generate_alerts(
    crypto: dict[str, Any],
    stocks: dict[str, Any],
    threshold: float,
) -> list[dict[str, Any]]:
    """根據閾值生成警報列表。

    Args:
        crypto: 加密貨幣數據字典。
        stocks: 股票數據字典。
        threshold: 觸發警報的變化率閾值（%）。

    Returns:
        觸發警報的列表。
    """
    alerts: list[dict[str, Any]] = []
    for symbol, data in {**crypto, **stocks}.items():
        change = data["change_24h"]
        if abs(change) >= threshold:
            alert_type = "rise" if change > 0 else "drop"
            alerts.append(
                {
                    "symbol": symbol.upper(),
                    "type": data["type"],
                    "name": data["name"],
                    "alert_type": alert_type,
                    "change": change,
                    "threshold": threshold,
                    "triggered": True,
                }
            )
    return alerts


def print_report(
    crypto: dict[str, Any],
    stocks: dict[str, Any],
    alerts: list[dict[str, Any]],
) -> None:
    """在終端輸出格式化的資產價格報告。

    Args:
        crypto: 加密貨幣數據字典。
        stocks: 股票數據字典。
        alerts: 警報列表。
    """
    print("\n💰 加密貨幣")
    print("-" * 50)
    print(f"{'幣種':<8} {'名稱':<12} {'價格 (USD)':>14} {'24h 變化':>10}")
    print("-" * 50)
    for symbol, data in crypto.items():
        icon = "🔺" if data["change_24h"] >= 0 else "🔻"
        print(
            f"{symbol.upper():<8} {data['name']:<12} "
            f"${data['usd']:>13,.2f} {icon} {data['change_24h']:>+.2f}%"
        )
    print("-" * 50)

    if stocks:
        print("\n📈 美股 ETF")
        print("-" * 55)
        print(f"{'代號':<8} {'名稱':<14} {'價格 (USD)':>14} {'24h 變化':>10}")
        print("-" * 55)
        for symbol, data in stocks.items():
            icon = "🔺" if data["change_24h"] >= 0 else "🔻"
            print(
                f"{symbol.upper():<8} {data['name']:<14} "
                f"${data['usd']:>13,.2f} {icon} {data['change_24h']:>+.2f}%"
            )
        print("-" * 55)

    if alerts:
        print(f"\n🚨 警報：{len(alerts)} 個事件觸發")
        for alert in alerts:
            if alert.get("alert_type") == "indicator_alert":
                print(f"  • [技術指標] {alert['symbol']} 觸發訊號：{alert['signal_reason']}")
            else:
                direction = "上漲" if alert["alert_type"] == "rise" else "下跌"
                print(
                    f"  • [{alert['type']}] {alert['symbol']} ({alert['name']}) "
                    f"{direction}超過 {alert['threshold']}%（{alert['change']:+.2f}%）"
                )
    else:
        print("\n✅ 無警報觸發")
    print()


def backfill_ohlcv() -> None:
    """透過 yfinance 一次性回溯抓取一個月的日 K 線資料寫入 SQLite。"""
    if yf is None:
        print("⚠️ yfinance 未安裝，無法回溯 OHLCV 資料。")
        return
        
    records = []
    
    # 處理加密貨幣 (yfinance ticker: BTC-USD, ETH-USD 等)
    for symbol in COIN_MAP.values():
        ticker = f"{symbol.upper()}-USD"
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1mo")
            for index, row in hist.iterrows():
                date_str = index.strftime('%Y-%m-%d')
                records.append((
                    date_str,
                    symbol.upper(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Volume'])
                ))
        except Exception as e:
            print(f"⚠️ 獲取 {ticker} 歷史 K 線失敗: {e}")
            
    # 處理美股 ETF
    for ticker in ETF_MAP.keys():
        try:
            t = yf.Ticker(ticker, session=session)
            hist = t.history(period="1mo")
            for index, row in hist.iterrows():
                date_str = index.strftime('%Y-%m-%d')
                records.append((
                    date_str,
                    ticker.upper(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Volume'])
                ))
        except Exception as e:
            print(f"⚠️ 獲取 {ticker} 歷史 K 線失敗: {e}")
            
    if records:
        print(f"🔄 準備寫入 {len(records)} 筆歷史 OHLCV 資料...")
        database.insert_ohlcv_batch(records)


def main() -> None:
    """主程序入口。"""
    threshold = float(os.getenv("THRESHOLD", "2.0"))
    print(f"🔄 正在抓取資產價格（閾值: {threshold}%）...")

    crypto: dict[str, Any] = {}
    stocks: dict[str, Any] = {}

    # 抓取加密貨幣數據
    try:
        raw_crypto = fetch_crypto_prices()
        crypto = process_crypto_prices(raw_crypto)
    except requests.RequestException as e:
        print(f"⚠️  警告：加密貨幣 API 請求失敗：{e}")
    except Exception as e:
        print(f"⚠️  警告：加密貨幣數據處理失敗：{e}")

    # 抓取股票數據
    stocks = fetch_stock_prices()

    alerts = generate_alerts(crypto, stocks, threshold)
    
    # 進行技術指標分析掃描 (RSI, MACD)
    ta_signals = indicator_analyzer.get_ta_signals(crypto, stocks)
    for symbol, res in ta_signals.items():
        # 如果有特別訊號(如超買超賣)，加入警報中
        alerts.append({
            "symbol": symbol.upper(),
            "type": "TA_SIGNAL",
            "name": f"{symbol} 技術指標",
            "alert_type": "indicator_alert",
            "change": 0.0, # 不是因為漲跌幅觸發的
            "threshold": 0.0,
            "triggered": True,
            "signal_reason": res["signal"]
        })

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "crypto": crypto,
        "stocks": stocks,
        "ta_signals": ta_signals,
        "alerts": alerts,
    }

    with open("asset_status.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print_report(crypto, stocks, alerts)
    print("✅ 數據已保存至 asset_status.json")

    # 寫入歷史資料庫
    try:
        database.init_db()
        database.insert_prices(output["timestamp"], crypto, stocks)
        
        # 追加回溯並寫入 OHLCV 日 K 線資料
        backfill_ohlcv()
    except Exception as e:
        print(f"⚠️  警告：寫入歷史資料庫失敗：{e}")


if __name__ == "__main__":
    main()
