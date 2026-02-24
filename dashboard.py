"""
Crypto & Stock Monitor Streamlit Dashboard
提供即時資產價格監控狀態，以及歷史價格趨勢檢視。
"""

import json
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. 設置頁面標題與佈局
st.set_page_config(page_title="資產價格監控看板", page_icon="📈", layout="wide")
st.title("📈 資產價格監控看板")

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
        df = pd.read_sql_query("SELECT * FROM asset_prices", conn)
        conn.close()
        # 將字串格式的時間轉為 datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"無法讀取歷史資料庫: {e}")
        return pd.DataFrame()

status_data = load_latest_status()
history_df = load_historical_data()

# 4. 顯示最新即時概況 (Metrics)
st.header("⚡ 最新資產概況", divider="gray")
if status_data:
    st.write(f"**最後更新時間**：{status_data.get('timestamp')}")
    
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

# 5. 歷史趨勢圖 (Plotly)
st.header("📊 歷史價格趨勢", divider="gray")
if not history_df.empty and len(history_df) > 0:
    st.write("透過點擊右側圖例可以隱藏或顯示特定資產")
    
    assets = history_df['symbol'].unique()
    selected_assets = st.multiselect("選擇要在圖表中顯示的資產", options=assets, default=assets)
    
    if selected_assets:
        filtered_df = history_df[history_df['symbol'].isin(selected_assets)]
        
        # 繪製 Plotly 圖表
        fig = px.line(
            filtered_df,
            x="timestamp",
            y="usd_price",
            color="symbol",
            markers=True,
            title="資產價格變動趨勢",
            labels={"usd_price": "價格 (USD)", "timestamp": "時間"},
        )
        # 如果資產價格範圍差太多，推薦使用者可以分別點擊或開對數座標，這裡給個選項
        use_log = st.checkbox("使用對數座標 (幫助同時觀察比特幣與小幣/ETF 的價格波動)")
        if use_log:
            fig.update_layout(yaxis_type="log")
            
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("歷史資料庫目前沒有足夠的數據可供趨勢分析。")

# --- Footer ---
st.caption("powered by Antigravity & Streamlit, made for Coilpot tutorial equivalent.")
