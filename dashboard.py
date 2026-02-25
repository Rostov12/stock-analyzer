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
    
    # 建立三個分頁
    tab1, tab2, tab3 = st.tabs(["加密貨幣 (Crypto)", "美股 ETF (Stocks)", "📈 AI 智能報告"])
    
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
            stock_items = list(stock_data.items())
            # 動態計算每列欄數，避免超出
            cols_per_row = min(4, len(stock_items))
            for row_start in range(0, len(stock_items), cols_per_row):
                row_items = stock_items[row_start:row_start + cols_per_row]
                cols = st.columns(len(row_items))
                for j, (symbol, data) in enumerate(row_items):
                    cols[j].metric(
                        label=f"{symbol.upper()} ({data['name']})",
                        value=f"${data['usd']:,.2f}",
                        delta=f"{data['change_24h']}%",
                    )
        else:
            st.info("目前沒有美股 ETF 數據。請點擊上方的「🔄 手動更新」按鈕抓取資料。")
            
    with tab3:
        st.subheader("🤖 AI 金融分析師")
        st.write("點擊下方按鈕，系統將即時抓取最新報價，並交由 `Gemini-2.5-Flash` 撰寫專業分析報告。")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            btn_us_intra = st.button("產出【美股盤中快報】")
        with col_r2:
            btn_us_close = st.button("產出【美股盤後總結】")
        with col_r3:
            btn_uranium = st.button("產出【鈾礦與核能專題】")
            
        if btn_us_intra:
            with st.spinner("AI 正在分析美股盤中數據..."):
                import report_generator
                res = report_generator.generate_us_intraday_report()
                st.session_state["last_report"] = res
        if btn_us_close:
            with st.spinner("AI 正在分析美股盤後數據..."):
                import report_generator
                res = report_generator.generate_us_close_report()
                st.session_state["last_report"] = res
        if btn_uranium:
            with st.spinner("AI 正在深度分析鈾礦板塊..."):
                import report_generator
                res = report_generator.generate_uranium_report()
                st.session_state["last_report"] = res
                
        if "last_report" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["last_report"])
            if st.button("📲 將此報告傳送至我的 Telegram", type="primary"):
                import report_generator
                with st.spinner("發送中..."):
                    send_res = report_generator.send_telegram_report(st.session_state["last_report"])
                    if "✅" in send_res:
                        st.success(send_res)
                    else:
                        st.error(send_res)
                
    # 警報區塊
    alerts = status_data.get("alerts", [])
    if alerts:
        st.error(f"🚨 觸發了 {len(alerts)} 筆警報！")
        for alert in alerts:
            if alert.get("alert_type") == "indicator_alert":
                st.warning(f"⚠️ [技術指標] **{alert['symbol']}** 觸發：{alert.get('signal_reason', '未知')}")
            else:
                direction = "🔺 上漲" if alert["alert_type"] == "rise" else "🔻 下跌"
                st.warning(f"{alert['type'].upper()} **{alert['symbol']}** {direction} 超過 {alert['threshold']}% (當前: {alert['change']:+.2f}%)")

else:
    st.warning("找不到 `asset_status.json`，請先執行監控腳本抓取資料。")

# 5. 歷史趨勢圖 (互動式 Plotly Candlestick)
st.header("📊 歷史 K 線圖 (Candlestick)", divider="gray")
if not history_df.empty and len(history_df) > 0:
    valid_assets = history_df['symbol'].dropna().unique()
    
    if len(valid_assets) > 0:
        selected_asset = st.selectbox("選擇要檢視 K 線的資產", options=valid_assets)
        
        if selected_asset:
            # 取最近 30 筆，控制 JSON 大小
            filtered_df = history_df[history_df['symbol'] == selected_asset].copy()
            filtered_df = filtered_df.sort_values('date', ascending=False).head(30)
            filtered_df = filtered_df.sort_values('date', ascending=True)
            filtered_df = filtered_df.dropna(subset=['open', 'high', 'low', 'close', 'date'])
            
            if not filtered_df.empty:
                try:
                    # 將數值強制轉為 Python float，避免 numpy 型別造成 JSON 序列化問題
                    dates = filtered_df['date'].dt.strftime('%Y-%m-%d').tolist()
                    opens = [float(v) for v in filtered_df['open']]
                    highs = [float(v) for v in filtered_df['high']]
                    lows = [float(v) for v in filtered_df['low']]
                    closes = [float(v) for v in filtered_df['close']]
                    
                    fig = go.Figure(data=[go.Candlestick(
                        x=dates,
                        open=opens,
                        high=highs,
                        low=lows,
                        close=closes,
                        increasing_line_color='#ef5350',  # 紅漲
                        decreasing_line_color='#26a69a',  # 綠跌
                    )])
                    
                    fig.update_layout(
                        title=f"{selected_asset} 最近 30 日 K 線圖",
                        yaxis_title="Price (USD)",
                        xaxis_rangeslider_visible=False,  # 關閉底部導覽列以減少 JSON
                        height=450,
                        margin=dict(l=40, r=40, t=40, b=40),
                        template="plotly_dark",
                    )
                    
                    # 使用 use_container_width 讓圖表自適應
                    st.plotly_chart(fig, width='stretch')
                    
                except Exception as e:
                    st.error(f"⚠️ 繪製圖表時發生錯誤：{e}")
            else:
                st.warning("該資產目前沒有有效的 OHLCV 數據可供繪製。")
    else:
        st.info("資料庫中沒有找到有效的資產符號。")
else:
    st.info("歷史資料庫 `asset_ohlcv` 目前沒有數據。請點擊「手動更新」來抓取過去三十天的歷史報價。")

# 6. 買賣交易手動登錄
st.header("📝 新增買賣交易紀錄", divider="gray")
with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tx_date = st.date_input("交易日期", value=pd.Timestamp.now().date())
        tx_symbol = st.text_input("資產代號 (例如 BTC, URNM)").upper()
        tx_type = st.selectbox("買賣別", ["BUY", "SELL"])
    with col2:
        tx_price = st.number_input("成交單價", min_value=0.0, format="%.4f")
        tx_quantity = st.number_input("成交數量", min_value=0.0, format="%.4f")
        tx_notes = st.text_input("備註 (選填)")
        
    submitted = st.form_submit_button("💾 儲存紀錄")
    
    if submitted:
        if tx_symbol and tx_price > 0 and tx_quantity > 0:
            try:
                database.insert_transaction(
                    timestamp=tx_date.strftime("%Y-%m-%d"),
                    symbol=tx_symbol,
                    transaction_type=tx_type,
                    price=tx_price,
                    quantity=tx_quantity,
                    notes=tx_notes if tx_notes else "Dashboard Web UI 手動登錄"
                )
                st.success(f"✅ 成功寫入紀錄: {tx_type} {tx_quantity} 股/枚 {tx_symbol} @ ${tx_price}")
            except Exception as e:
                st.error(f"⚠️ 寫入失敗: {e}")
        else:
            st.warning("⚠️ 請填寫完整的資產代號，且價格與數量必須大於 0。")

# --- Footer ---
st.caption("powered by Antigravity & Streamlit, made for Coilpot tutorial equivalent.")
