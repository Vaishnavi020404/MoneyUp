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

# Read symbols from DB — whatever user has added
c.execute("SELECT DISTINCT symbol FROM stock_prices")
symbols = [row[0] for row in c.fetchall()]

if not symbols:
    print("No stocks in DB yet. Add stocks from the dashboard first.")
else:
    for symbol in symbols:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            # Fetch only the latest trading day
            data = ticker.history(period="2d", interval="1d")

            if data.empty:
                print(f"No data for {symbol}")
                continue

            latest = data.iloc[-1]
            latest_dt = str(data.index[-1].date())

            c.execute("""
            INSERT OR IGNORE INTO stock_prices VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                latest_dt,
                float(latest["Open"]),
                float(latest["High"]),
                float(latest["Low"]),
                float(latest["Close"]),
                datetime.now().isoformat()
            ))

            print(f"✓ {symbol} — ₹{latest['Close']:.2f}")

        except Exception as e:
            print(f"✗ {symbol} failed: {e}")

conn.commit()
conn.close()
