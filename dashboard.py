"""
Crypto & Stock Monitor Streamlit Dashboard
提供即時資產價格監控狀態，以及歷史價格趨勢檢視。
"""

import json
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import subprocess
import sys
import transaction_parser
import database

# 1. 設置頁面標題與佈局
st.set_page_config(page_title="資產價格監控看板", page_icon="📈", layout="wide")
st.title("📈 資產價格監控看板")

# 1.1 手動觸發更新按鈕
if st.button("🔄 手動更新最新報價與歷史 K 線", help="這會在背景執行資料抓取，完成後請手動重新整理網頁。"):
    with st.spinner("資料抓取中 (預計 10-20 秒)，請稍候..."):
        try:
            import asset_monitor
            asset_monitor.main()
            st.success("✅ 資料已成功更新！畫面即將重新整理...")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 更新失敗: {e}")

# 2. 讀取最新狀態 JSON
@st.cache_data(ttl=60)
def load_latest_status():
    try:
        with open("asset_status.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# 3. 讀取歷史資料庫
def load_historical_data():
    try:
        conn = sqlite3.connect("crypto_monitor.db")
        df = pd.read_sql_query("SELECT * FROM asset_ohlcv ORDER BY date ASC", conn)
        conn.close()
        # 轉換日期
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"無法讀取 OHLCV 歷史資料庫: {e}")
        return pd.DataFrame()

status_data = load_latest_status()
history_df = load_historical_data()

# 4. 顯示最新即時概況 (Metrics)
st.header("⚡ 最新資產概況", divider="gray")
if status_data:
    try:
        from dateutil import parser
        from datetime import timedelta
        # 將 UTC 字串轉為 datetime 物件，然後加上 8 小時轉為台北時間
        utc_time = parser.parse(status_data.get('timestamp', ''))
        taipei_time = utc_time + timedelta(hours=8)
        formatted_time = taipei_time.strftime("%Y年-%m月-%d日 %H:%M")
    except Exception:
        # 如果解析失敗，退回預設顯示
        formatted_time = status_data.get('timestamp')
        
    st.write(f"**最後更新時間**：{formatted_time} (台北時間)")
    
    # 建立兩個分頁，一個放 Crypto，一個放 Stock
    tab1, tab2 = st.tabs(["加密貨幣 (Crypto)", "美股 ETF (Stocks)"])
    
    with tab1:
        crypto_data = status_data.get("crypto", {})
        cols = st.columns(len(crypto_data) if crypto_data else 1)
        for i, (symbol, data) in enumerate(crypto_data.items()):
            cols[i].metric(
                label=f"{symbol.upper()} ({data['name']})",
                value=f"${data['usd']:,.2f}",
                delta=f"{data['change_24h']}%",
                delta_color="normal" # Streamlit 會自動把正變綠，負變紅
            )
            
    with tab2:
        stock_data = status_data.get("stocks", {})
        if stock_data:
            # 每列顯示四個
            cols = st.columns(4)
            for i, (symbol, data) in enumerate(stock_data.items()):
                cols[i % 4].metric(
                    label=f"{symbol.upper()} ({data['name']})",
                    value=f"${data['usd']:,.2f}",
                    delta=f"{data['change_24h']}%",
                )
        else:
            st.info("目前沒有美股 ETF 數據。")
            
    # 警報區塊
    alerts = status_data.get("alerts", [])
    if alerts:
        st.error(f"🚨 觸發了 {len(alerts)} 筆警報！")
        for alert in alerts:
            direction = "🔺 上漲" if alert["alert_type"] == "rise" else "🔻 下跌"
            st.warning(f"{alert['type'].upper()} **{alert['symbol']}** {direction} 超過 {alert['threshold']}% (當前: {alert['change']:+.2f}%)")

else:
    st.warning("找不到 `asset_status.json`，請先執行監控腳本抓取資料。")

# 5. 歷史趨勢圖 (Candlestick)
st.header("📊 歷史 K 線圖 (Candlestick)", divider="gray")
if not history_df.empty and len(history_df) > 0:
    valid_assets = history_df['symbol'].dropna().unique()
    
    if len(valid_assets) > 0:
        # K 線圖通常單獨檢視比較清楚
        selected_asset = st.selectbox("選擇要檢視 K 線的資產", options=valid_assets)
        
        if selected_asset:
            filtered_df = history_df[history_df['symbol'] == selected_asset].copy()
            # 確保不會有 NaN 丟給前端，導致 JSON 轉換錯誤
            filtered_df = filtered_df.dropna(subset=['open', 'high', 'low', 'close', 'date'])
            
            if not filtered_df.empty:
                try:
                    fig = go.Figure(data=[go.Candlestick(
                        x=filtered_df['date'],
                        open=filtered_df['open'],
                        high=filtered_df['high'],
                        low=filtered_df['low'],
                        close=filtered_df['close'],
                        name=selected_asset
                    )])
                    
                    fig.update_layout(
                        title=f"{selected_asset} 歷史日 K 線圖",
                        yaxis_title="價格 (USD)",
                        xaxis_title="日期",
                        xaxis_rangeslider_visible=False, # 關閉底部的範圍選擇器讓圖表更乾淨
                        template="plotly_dark"
                    )
                        
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"⚠️ 繪製圖表時發生錯誤：{e}")
            else:
                st.warning("該資產目前沒有有效的 OHLCV 數據可供繪製。")
    else:
        st.info("資料庫中沒有找到有效的資產符號。")
else:
    st.info("歷史資料庫 `asset_ohlcv` 目前沒有數據。請點擊「手動更新」來抓取過去三十天的歷史報價。")

# 6. AI 交易截圖辨識入庫
st.header("📸 交易截圖手動上傳與 AI 辨識", divider="gray")
uploaded_file = st.file_uploader("請上傳一張交易明細截圖 (支援口袋證券等)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    if st.button("🚀 開始辨識並寫入資料庫"):
        with st.spinner("AI 正在努力閱讀截圖中的數字..."):
            bytes_data = uploaded_file.getvalue()
            result = transaction_parser.parse_transaction_image(bytes_data)
            
            if result:
                # 寫入資料庫
                try:
                    database.insert_transaction(
                        timestamp=str(result["timestamp"]),
                        symbol=str(result["symbol"]),
                        transaction_type=str(result["transaction_type"]),
                        price=float(result["price"]),
                        quantity=float(result["quantity"]),
                        notes="Dashboard Web UI 上傳辨識"
                    )
                    st.success("✅ 記錄已成功自動寫入資料庫！")
                    st.json(result)
                except Exception as db_e:
                    st.error(f"⚠️ 寫入資料庫失敗：{db_e}")
            else:
                st.error("❌ 抱歉，AI 辨識失敗或找不到完整的買賣資訊。請確保金鑰正確且圖片清晰。")

# --- Footer ---
st.caption("powered by Antigravity & Streamlit, made for Coilpot tutorial equivalent.")
