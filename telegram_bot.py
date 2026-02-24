"""
進階 Telegram 機器人
提供互動式指令查詢資產價格與警示狀態。
"""

import json
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_status_data():
    """讀取最新的 asset_status.json"""
    try:
        with open('asset_status.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    await update.message.reply_text(
        "👋 歡迎使用資產監控機器人 (Crypto Monitor)！\n\n"
        "您可以使用以下指令：\n"
        "👉 /status - 查詢最新資產價格狀態\n"
        "👉 /alerts - 查詢目前已觸發的警報與技術指標訊號"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /status 指令，回報最新價格與技術指標"""
    data = load_status_data()
    if not data:
        await update.message.reply_text("❌ 目前找不到價格數據，請確定 `asset_monitor.py` 已經執行過。")
        return

    # 構建加密貨幣列表
    crypto_lines = []
    for symbol, info in data.get('crypto', {}).items():
        emoji = "📈" if info['change_24h'] >= 0 else "📉"
        sign = "+" if info['change_24h'] >= 0 else ""
        crypto_lines.append(
            f"{emoji} <b>{symbol.upper()}</b>: ${info['usd']:,.2f} ({sign}{info['change_24h']}%)"
        )

    # 構建美股列表
    stock_lines = []
    for symbol, info in data.get('stocks', {}).items():
        emoji = "📈" if info['change_24h'] >= 0 else "📉"
        sign = "+" if info['change_24h'] >= 0 else ""
        stock_lines.append(
            f"{emoji} <b>{symbol.upper()}</b>: ${info['usd']:,.2f} ({sign}{info['change_24h']}%)"
        )

    message_parts = [
        "🚀 <b>最新資產價格監控報告</b> 📊",
        "",
        f"⏰ 時間: {data.get('timestamp')}",
        "",
        "💰 <b>加密貨幣:</b>",
        *crypto_lines,
        "",
        "📈 <b>美股 ETF:</b>",
        *stock_lines,
    ]

    message = "\n".join(message_parts)
    await update.message.reply_text(message, parse_mode='HTML')

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /alerts 指令"""
    data = load_status_data()
    if not data:
        await update.message.reply_text("❌ 目前找不到數據。")
        return

    alerts = data.get('alerts', [])
    if not alerts:
        await update.message.reply_text("✅ 目前沒有任何資產觸發警報或技術指標訊號。")
        return

    alert_lines = []
    for alert in alerts:
        if alert.get("alert_type") == "indicator_alert":
            alert_lines.append(f"⚠️ [技術指標] <b>{alert['symbol']}</b> 觸發：{alert['signal_reason']}")
        else:
            direction = "🔺上漲" if alert["alert_type"] == "rise" else "🔻下跌"
            alert_lines.append(
                f"🚨 [{alert['type'].upper()}] <b>{alert['symbol']}</b> {direction} 超過 {alert['threshold']}% "
                f"(當前: {alert['change']:+.2f}%)"
            )

    message = f"🚨 <b>目前共有 {len(alerts)} 個警報觸發：</b>\n\n" + "\n".join(alert_lines)
    await update.message.reply_text(message, parse_mode='HTML')

def main():
    # 改從環境變數讀取，或者可以直接填入這裡
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '8589611809:AAGpQAQ3usjx8_9XTOKvpuEW9TkrMZYiwXU')
    
    if bot_token == '8589611809:AAGpQAQ3usjx8_9XTOKvpuEW9TkrMZYiwXU':
        logging.info("使用預設的 Telegram Bot Token 進行啟動。")
        # return

    # 建立應用程式，這裡為了示範即使無 token 也先建置結構，但執行會報錯
    try:
        application = ApplicationBuilder().token(bot_token).build()

        # 註冊指令
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("alerts", alerts_command))

        logging.info("🤖 機器人已啟動，開始接收指令...")
        # 開始輪詢接收訊息
        application.run_polling()
        
    except Exception as e:
        logging.error(f"啟動機器人失敗 (如果沒有設定 Token 會報 TokenInvalid 錯誤): {e}")

if __name__ == '__main__':
    main()
