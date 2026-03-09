import yfinance as yf
import sqlite3
import os
from datetime import datetime

SYMBOLS = [
    "BANDHANBNK.NS", "CGPOWER.NS", "COALINDIA.NS", "COCHINSHIP.NS",
    "IDEA.NS", "IRCON.NS", "SUZLON.NS", "TCS.NS", "YESBANK.NS"
]

os.makedirs("../database", exist_ok=True)
conn = sqlite3.connect("../database/stock_data.db")
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

for symbol in SYMBOLS:
    try:
        ticker = yf.Ticker(symbol)
        # Daily OHLC from Jan 1 2026 to today
        data = ticker.history(start="2026-01-01", end=datetime.today().strftime("%Y-%m-%d"), interval="1d")

        if data.empty:
            print(f"No data for {symbol}")
            continue

        for dt, row in data.iterrows():
            c.execute("""
            INSERT OR IGNORE INTO stock_prices VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol.replace(".NS", ""),
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
