import yfinance as yf
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_data.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS stock_prices (
    symbol TEXT,
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    fetched_at TEXT,
    PRIMARY KEY (symbol, datetime)
)
""")

SYMBOLS = ["RELIANCE"]

for symbol in SYMBOLS:
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(start="2026-01-01", end=datetime.today().strftime("%Y-%m-%d"), interval="1d")

        if data.empty:
            print(f"No data for {symbol}")
            continue

        for dt, row in data.iterrows():
            c.execute("INSERT OR IGNORE INTO stock_prices VALUES (?,?,?,?,?,?,?)", (
                symbol,
                str(dt.date()),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                datetime.now().isoformat()
            ))

        print(f"✓ {symbol} — {len(data)} days loaded")

    except Exception as e:
        print(f"✗ {symbol} failed: {e}")

conn.commit()
conn.close()
