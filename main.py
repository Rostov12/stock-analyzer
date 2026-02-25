import os
import sys
import subprocess
import time
import threading
import schedule
import pytz
from datetime import datetime

def run_monitor():
    print(f"[{datetime.now()}] 執行定時資料更新與 AI 警報任務...")
    subprocess.run([sys.executable, "asset_monitor.py"])
    print(f"[{datetime.now()}] 定時更新完成。")

def schedule_worker():
    # 使用 TZ 環境變數，或是直接指定 Taipei 時區
    try:
        schedule.every().day.at("06:00", "Asia/Taipei").do(run_monitor)
        print("✅ 已設定每日 06:00 (Asia/Taipei) 自動執行資料更新")
    except Exception as e:
        print(f"⚠️ 排程設定時區失敗，改用 UTC 22:00 作為備案 ({e})")
        schedule.every().day.at("22:00").do(run_monitor)

    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    print("🚀 Starting Crypto Monitor Services...")
    
    # 啟動自動排程背景執行緒 (守護執行緒讓主程式退出時也跟著退出)
    scheduler_thread = threading.Thread(target=schedule_worker, daemon=True)
    scheduler_thread.start()
    
    # 啟動 Telegram Bot
    # 就算設定錯誤也不要讓他馬上掛掉，這只是其中一個服務
    print("-> Starting Telegram Bot...")
    bot_process = subprocess.Popen([sys.executable, "telegram_bot.py"])
    
    # 啟動 Streamlit Dashboard
    port = os.environ.get("PORT", "8080")
    print(f"-> Starting Streamlit Dashboard on port {port}...")
    dashboard_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "dashboard.py", 
        "--server.port", port, 
        "--server.address", "0.0.0.0"
    ])
    
    # 保持主行程常駐，避免 Docker 容器退出
    try:
        bot_process.wait()
        dashboard_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        bot_process.terminate()
        dashboard_process.terminate()

if __name__ == "__main__":
    main()
