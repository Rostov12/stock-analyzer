import os
import sys
import subprocess
import time

def main():
    print("🚀 Starting Crypto Monitor Services...")
    
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
