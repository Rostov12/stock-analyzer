"""
發送 Telegram 通知腳本
"""
import json
import os
import sys
from datetime import datetime

import requests

def send_telegram_notification():
    """發送資產監控報告到 Telegram"""
    try:
        # 讀取數據
        with open('asset_status.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 構建加密貨幣列表
        crypto_lines = []
        for symbol, info in data.get('crypto', {}).items():
            emoji = "📈" if info['change_24h'] >= 0 else "📉"
            sign = "+" if info['change_24h'] >= 0 else ""
            crypto_lines.append(
                f"{emoji} <b>{symbol.upper()}</b>: ${info['usd']} ({sign}{info['change_24h']}%)"
            )

        # 構建美股列表
        stock_lines = []
        for symbol, info in data.get('stocks', {}).items():
            emoji = "📈" if info['change_24h'] >= 0 else "📉"
            sign = "+" if info['change_24h'] >= 0 else ""
            stock_lines.append(
                f"{emoji} <b>{symbol.upper()}</b> ({info['name']}): ${info['usd']} ({sign}{info['change_24h']}%)"
            )

        # 警報狀態
        alert_count = len(data.get('alerts', []))
        alert_text = f"🚨 {alert_count} 個警報觸發" if alert_count > 0 else "✅ 無警報"

        # 構建完整訊息
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        repo_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', 'Rostov12/crypto-monitor')}"

        message_parts = [
            "🚀 <b>資產價格監控報告</b> 📊",
            "",
            f"⏰ 時間: {timestamp}",
            "",
            "💰 <b>加密貨幣:</b>",
            *crypto_lines,
            "",
            "📈 <b>美股 ETF:</b>",
            *stock_lines,
            "",
            alert_text,
            "",
            f"📊 <a href='{repo_url}/blob/main/asset_status.json'>查看詳細報告</a>"
        ]

        message = "\n".join(message_parts)

        # 發送到 Telegram
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("⚠️ 警告：缺少 Telegram 憑證，跳過通知")
            return

        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Telegram 通知發送成功")
        else:
            print(f"❌ Telegram 通知發送失敗: {response.status_code}")
            print(response.text)

    except FileNotFoundError:
        print("❌ 找不到 asset_status.json 文件")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 發送通知時出錯: {e}")
        sys.exit(1)


if __name__ == "__main__":
    send_telegram_notification()