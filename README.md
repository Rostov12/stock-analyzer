# 📊 資產價格監控系統

自動化資產價格監控系統，同時追蹤加密貨幣和美股 ETF，使用 GitHub Actions 定期抓取最新價格並以 JSON 格式輸出報告。

---

## ✨ 功能特點

- 📈 自動監控 4 種加密貨幣 + 7 支美股 ETF
- ⏰ 智能排程：美股交易時間和非交易時間不同頻率
- 📄 JSON 格式輸出，包含價格與 24h 漲跌
- 🚨 可自訂閾值的警報系統
- 🔔 雙重通知：Telegram 實時推送
- 🆓 免費數據源（CoinGecko 公開 API + Yahoo Finance）

---

## 🪙 監控的資產

### 加密貨幣

| 代號 | 名稱 |
|------|------|
| BTC | Bitcoin |
| ETH | Ethereum |
| SOL | Solana |
| ADA | Cardano |

### 美股 ETF

| 代號 | 名稱 |
|------|------|
| SMH | 半導體 ETF |
| AIQ | 人工智慧 ETF |
| BOTZ | 機器人 ETF |
| URNM | 鈾礦 ETF |
| NLR | 核能 ETF |
| GLD | 黃金 ETF |
| CPER | 銅 ETF |

---

## 🚀 使用方式

### 1. 自動執行

Workflow 依照智能排程自動執行：

- **週一至週五（美股交易時間）**：UTC 15:00、17:00、19:00、21:00
- **週末**：每 6 小時（僅加密貨幣有價格更新）

### 2. 手動觸發

1. 前往 GitHub 儲存庫的 **Actions** 頁籤
2. 在左側選擇 **資產價格監控（加密貨幣 + 美股）** workflow
3. 點擊右側 **Run workflow** 按鈕
4. 可選填警報閾值（預設 `2.0`，代表 ±2%）
5. 點擊綠色 **Run workflow** 確認執行

### 3. 查看結果

**方式一：直接查看 JSON 文件**

執行完成後，`asset_status.json` 會自動提交回 `main` branch，可直接在儲存庫中查看。

**方式二：查看 Workflow Summary**

進入 Actions → 選取某次執行 → 在 Summary 區塊可見格式化的 JSON 報告。

**方式三：下載 Artifacts**

進入 Actions → 選取某次執行 → 在頁面底部 **Artifacts** 區塊下載 `asset-status-<run_number>.zip`，Artifacts 保留 30 天。

---

## 📄 JSON 輸出範例

```json
{
  "timestamp": "2026-02-19T22:30:45.123456+00:00",
  "crypto": {
    "btc": {
      "type": "crypto",
      "name": "Bitcoin",
      "usd": 98234.56,
      "change_24h": 2.34
    },
    "eth": {
      "type": "crypto",
      "name": "Ethereum",
      "usd": 3456.78,
      "change_24h": -1.23
    }
  },
  "stocks": {
    "smh": {
      "type": "stock",
      "name": "半導體ETF",
      "usd": 215.34,
      "change_24h": 1.25
    }
  },
  "alerts": [
    {
      "symbol": "BTC",
      "type": "crypto",
      "name": "Bitcoin",
      "alert_type": "rise",
      "change": 2.34,
      "threshold": 2.0,
      "triggered": true
    }
  ]
}
```

| 欄位 | 說明 |
|------|------|
| `timestamp` | 資料抓取時間（UTC，ISO 8601 格式） |
| `crypto.<symbol>.usd` | 加密貨幣當前美元價格 |
| `crypto.<symbol>.change_24h` | 24 小時漲跌幅（%） |
| `stocks.<symbol>.usd` | ETF 當前美元價格 |
| `stocks.<symbol>.change_24h` | 相較前一交易日的變化率（%） |
| `alerts[].symbol` | 觸發警報的資產代號 |
| `alerts[].type` | `crypto` 或 `stock` |
| `alerts[].alert_type` | `rise`（上漲）或 `drop`（下跌） |
| `alerts[].threshold` | 觸發警報的閾值（%） |
| `alerts[].triggered` | 是否已觸發（固定為 `true`） |

---

## ⚙️ 進階配置

### 自訂警報閾值

**臨時（單次）：** 手動觸發時在 `threshold` 輸入框填入自訂值。

**永久：** 設定環境變數 `THRESHOLD`，或在 workflow 中修改預設值。

### 添加更多幣種

編輯 `asset_monitor.py` 中的 `COIN_MAP` 和 `COIN_NAMES`：

```python
COIN_MAP: dict[str, str] = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "solana": "sol",
    "cardano": "ada",
    "dogecoin": "doge",   # 新增 DOGE
}

COIN_NAMES: dict[str, str] = {
    "btc": "Bitcoin",
    "eth": "Ethereum",
    "sol": "Solana",
    "ada": "Cardano",
    "doge": "Dogecoin",   # 新增
}
```

### 添加更多 ETF

編輯 `asset_monitor.py` 中的 `ETF_MAP`：

```python
ETF_MAP: dict[str, str] = {
    "SMH": "半導體ETF",
    "QQQ": "納斯達克100 ETF",  # 新增
}
```

---

## ⚠️ 注意事項

- 美股數據僅在交易時間更新（週一至週五）
- 週末和假日股票價格不會有新的變化
- 加密貨幣 24/7 持續監控
- 股票價格變化基於最近兩個交易日比較

---

## 🛠️ 技術棧

| 技術 | 用途 |
|------|------|
| Python 3.11+ | 核心監控腳本 |
| GitHub Actions | 自動化排程與執行 |
| CoinGecko API | 免費加密貨幣價格數據源 |
| Yahoo Finance（yfinance） | 美股 ETF 價格數據源 |
| `requests` | HTTP 請求庫 |

---

## 📜 授權

[MIT License](LICENSE)
