"""
加密貨幣價格監控腳本
自動抓取 BTC, ETH, SOL, ADA 的價格數據並生成 JSON 報告。
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import requests

# 幣種映射
COIN_MAP: dict[str, str] = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "solana": "sol",
    "cardano": "ada",
}

API_URL = "https://api.coingecko.com/api/v3/simple/price"


def fetch_prices() -> dict[str, Any]:
    """從 CoinGecko API 抓取加密貨幣價格。"""
    params = {
        "ids": ",".join(COIN_MAP.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def process_prices(raw: dict[str, Any]) -> dict[str, Any]:
    """處理原始 API 數據，格式化為目標結構。"""
    prices: dict[str, Any] = {}
    for coin_id, symbol in COIN_MAP.items():
        data = raw.get(coin_id)
        if not data:
            print(f"⚠️  警告：API 未返回 {coin_id} 的數據，跳過")
            continue
        prices[symbol] = {
            "usd": round(data.get("usd", 0), 2),
            "change_24h": round(data.get("usd_24h_change", 0), 2),
        }
    return prices


def generate_alerts(prices: dict[str, Any], threshold: float) -> list[dict[str, Any]]:
    """根據閾值生成警報列表。"""
    alerts: list[dict[str, Any]] = []
    for symbol, data in prices.items():
        change = data["change_24h"]
        if abs(change) >= threshold:
            alert_type = "rise" if change > 0 else "drop"
            alerts.append(
                {
                    "coin": symbol.upper(),
                    "type": alert_type,
                    "threshold": threshold,
                    "triggered": True,
                }
            )
    return alerts


def print_report(prices: dict[str, Any], alerts: list[dict[str, Any]]) -> None:
    """在終端輸出格式化的價格報告。"""
    print("\n📊 加密貨幣價格報告")
    print("-" * 45)
    print(f"{'幣種':<8} {'價格 (USD)':>14} {'24h 變化':>10}")
    print("-" * 45)
    for symbol, data in prices.items():
        usd = data["usd"]
        change = data["change_24h"]
        icon = "🔺" if change >= 0 else "🔻"
        print(f"{symbol.upper():<8} ${usd:>13,.2f} {icon} {change:>+.2f}%")
    print("-" * 45)

    if alerts:
        print(f"\n🚨 警報：{len(alerts)} 個幣種觸發閾值")
        for alert in alerts:
            alert_type_text = "上漲" if alert["type"] == "rise" else "下跌"
            print(f"  • {alert['coin']} {alert_type_text}超過 {alert['threshold']}%")
    else:
        print("\n✅ 無警報觸發")
    print()


def main() -> None:
    """主程序入口。"""
    threshold = float(os.getenv("THRESHOLD", "2.0"))
    print(f"🔄 正在抓取加密貨幣價格（閾值: {threshold}%）...")

    try:
        raw_data = fetch_prices()
        prices = process_prices(raw_data)
        alerts = generate_alerts(prices, threshold)

        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prices": prices,
            "alerts": alerts,
        }

        with open("crypto_status.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print_report(prices, alerts)
        print("✅ 數據已保存至 crypto_status.json")

    except requests.RequestException as e:
        print(f"❌ API 請求失敗：{e}")
        raise
    except Exception as e:
        print(f"❌ 執行失敗：{e}")
        raise


if __name__ == "__main__":
    main()
