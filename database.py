"""
提供 SQLite 資料庫互動功能，用於儲存加密貨幣與美股 ETF 的歷史價格資料。
"""

import sqlite3
from typing import Any

DB_PATH = "crypto_monitor.db"

def init_db() -> None:
    """初始化資料庫與資料表。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            name TEXT NOT NULL,
            usd_price REAL NOT NULL,
            change_24h REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            transaction_type TEXT NOT NULL, -- BUY or SELL
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            total_value REAL NOT NULL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_prices(timestamp: str, crypto_data: dict[str, Any], stocks_data: dict[str, Any]) -> None:
    """
    將批次資產價格寫入 SQLite 資料庫。
    
    Args:
        timestamp: 資料抓取的時間標記 (ISO 8601 格式)。
        crypto_data: 處理後的加密貨幣資料字典。
        stocks_data: 處理後的股票資料字典。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    records = []
    
    for symbol, data in crypto_data.items():
        records.append((
            timestamp,
            symbol.upper(),
            data.get("type"),
            data.get("name"),
            data.get("usd"),
            data.get("change_24h")
        ))
        
    for symbol, data in stocks_data.items():
        records.append((
            timestamp,
            symbol.upper(),
            data.get("type"),
            data.get("name"),
            data.get("usd"),
            data.get("change_24h")
        ))
        
    cursor.executemany('''
        INSERT INTO asset_prices (timestamp, symbol, asset_type, name, usd_price, change_24h)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', records)
    
    conn.commit()
    conn.close()
    print(f"✅ 成功將 {len(records)} 筆資產價格寫入歷史資料庫。")

def insert_transaction(timestamp: str, symbol: str, transaction_type: str, price: float, quantity: float, notes: str = "") -> None:
    """
    新增一筆買賣交易紀錄。
    
    Args:
        timestamp: 交易時間 (ISO 8601 格式)。
        symbol: 交易標的代號 (例如 BTC, TSLA)。
        transaction_type: 交易類別 ('BUY' 或 'SELL')。
        price: 成交單價。
        quantity: 成交數量。
        notes: 備註 (選填)。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    total_value = price * quantity
    
    cursor.execute('''
        INSERT INTO transactions (timestamp, symbol, transaction_type, price, quantity, total_value, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, symbol.upper(), transaction_type.upper(), price, quantity, total_value, notes))
    
    conn.commit()
    conn.close()
    print(f"📝 記錄交易: {transaction_type.upper()} {quantity} {symbol.upper()} @ ${price}")

if __name__ == "__main__":
    init_db()
    print("資料庫初始化完成。")
